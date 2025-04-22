<template>
    <div class="sales-by-seller">
      <h1>Ventas por Asesor - {{ months[month - 1].name }} {{ year }}</h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="fetchData">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <label>Mes:</label>
        <select v-model="month" @change="fetchData">
          <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
        </select>
        <label>Estatus PDV:</label>
        <select v-model="status" @change="fetchData">
          <option value="Todos">Todos</option>
          <option value="Activo">Activo</option>
          <option value="Inactivo">Inactivo</option>
        </select>
        <label>Punto de Venta:</label>
        <select v-model="selectedPdv" @change="applyFilters">
          <option value="">Todos los PDVs</option>
          <option v-for="pdv in pdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
        </select>
        <label>Asesor:</label>
        <select v-model="selectedSeller" @change="applyFilters">
          <option value="">Todos los asesores</option>
          <option v-for="seller in filteredSellers" :key="seller" :value="seller">{{ seller }}</option>
        </select>
      </div>
  
      <!-- Botones para ordenar y exportar -->
      <div class="sort-buttons">
        <button @click="sortByName">Ordenar por Nombre</button>
        <button @click="sortByTotal">Ordenar por Total (Mayor a Menor)</button>
        <button @click="exportToExcel" :disabled="noData">Exportar a Excel</button>
      </div>
  
      <!-- Mensaje si no hay datos -->
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes y año seleccionados.
      </div>
  
      <!-- Tabla -->
      <div v-else class="table-container">
        <table class="sales-table">
          <thead>
            <tr>
              <th>Asesor</th>
              <th v-for="pdv in filteredPdvs" :key="pdv">{{ pdv }}</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredSalesData" :key="row.seller">
              <td>{{ row.seller }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv">{{ formatCurrency(row[pdv]) }}</td>
              <td>{{ formatCurrency(row.total) }}</td>
            </tr>
            <tr class="total-row" v-if="filteredSalesData.length > 0">
              <td>{{ totals.seller }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv">{{ formatCurrency(filteredTotals[pdv]) }}</td>
              <td>{{ formatCurrency(filteredTotals.total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Gráficos -->
      <div v-if="!noData" class="charts-container">
        <!-- Gráfico de Barras Horizontales: Top 10 Asesores Más Vendidos -->
        <div class="chart-wrapper">
          <h2>Top 10 Asesores Más Vendidos</h2>
          <Bar :data="horizontalBarChartData" :options="horizontalBarChartOptions" />
        </div>
  
        <!-- Gráfico de Dona: Distribución de Ventas por Asesor (Top 10) -->
        <div class="chart-wrapper">
          <h2>Distribución de Ventas (Top 10 Asesores)</h2>
          <Doughnut :data="doughnutChartData" :options="doughnutChartOptions" />
        </div>
  
        <!-- Gráfico de Barras: Desglose de Ventas por PDV para el Asesor Seleccionado -->
        <div v-if="selectedSeller" class="chart-wrapper">
          <h2>Ventas por PDV - {{ selectedSeller }}</h2>
          <Bar :data="pdvBreakdownChartData" :options="pdvBreakdownChartOptions" />
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed } from 'vue';
  import axios from '@/api/axios';
  import { Bar, Doughnut } from 'vue-chartjs';
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale,
    ArcElement
  } from 'chart.js';
  import * as XLSX from 'xlsx';
  import { saveAs } from 'file-saver';
  
  // Registrar los componentes de Chart.js
  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale,
    ArcElement
  );
  
  export default {
    name: 'SalesBySeller',
    components: {
      Bar,
      Doughnut
    },
    setup() {
      // Datos reactivos
      const year = ref(null);
      const years = ref([]);
      const currentDate = new Date();
      const currentMonth = currentDate.getMonth() + 1;
      const currentYear = currentDate.getFullYear();
      const month = ref(currentMonth); // Mes actual como predeterminado
      const months = ref([
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ]);
      const status = ref('Activo');
      const salesData = ref([]);
      const filteredSalesData = ref([]);
      const pdvs = ref([]);
      const sellers = ref([]);
      const totals = ref({});
      const selectedSeller = ref(''); // Filtro por asesor
      const selectedPdv = ref(''); // Filtro por PDV
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        const result = filteredSalesData.value.length > 0 && filteredSalesData.value.every(row => row.total === 0);
        console.log('noData:', result, 'filteredSalesData:', filteredSalesData.value);
        return result;
      });
  
      // Computed para PDVs filtrados (mostrar solo el PDV seleccionado o todos si no hay filtro)
      const filteredPdvs = computed(() => {
        if (selectedPdv.value) {
          return pdvs.value.filter(pdv => pdv === selectedPdv.value);
        }
        return pdvs.value;
      });
  
      // Computed para asesores filtrados (mostrar solo asesores que tienen ventas en el PDV seleccionado)
      const filteredSellers = computed(() => {
        if (selectedPdv.value) {
          return sellers.value.filter(seller => {
            const sellerData = salesData.value.find(row => row.seller === seller);
            return sellerData && sellerData[selectedPdv.value] > 0;
          });
        }
        return sellers.value;
      });
  
      // Computed para totales filtrados (ajustar los totales según los filtros)
      const filteredTotals = computed(() => {
        const result = { seller: 'TOTALES', total: 0 };
        filteredPdvs.value.forEach(pdv => {
          result[pdv] = 0;
          filteredSalesData.value.forEach(row => {
            result[pdv] += row[pdv];
          });
          result.total += result[pdv];
        });
        return result;
      });
  
      // Obtener los años disponibles con datos
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            fetchData();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          fetchData();
        }
      };
  
      // Obtener datos de ventas por asesor
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const response = await axios.get('/dashboard/sales-by-seller', {
            params: { year: year.value, month: month.value, status: status.value }
          });
          salesData.value = response.data.data || [];
          pdvs.value = response.data.pdvs || [];
          sellers.value = response.data.sellers || [];
          totals.value = response.data.totals || {};
          applyFilters(); // Aplicar filtros después de cargar los datos
          console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, sellers: sellers.value, totals: totals.value });
        } catch (error) {
          console.error('Error fetching sales by seller data:', error);
          salesData.value = [];
          filteredSalesData.value = [];
          pdvs.value = [];
          sellers.value = [];
          totals.value = {};
        }
      };
  
      // Aplicar filtros combinados (PDV y Asesor)
      const applyFilters = () => {
        let filtered = [...salesData.value];
  
        // Filtrar por PDV
        if (selectedPdv.value) {
          filtered = filtered.filter(row => row[selectedPdv.value] > 0);
        }
  
        // Filtrar por asesor
        if (selectedSeller.value) {
          filtered = filtered.filter(row => row.seller === selectedSeller.value);
        }
  
        filteredSalesData.value = filtered;
        sortByTotal(); // Ordenar por total después de filtrar
      };
  
      // Ordenar por nombre
      const sortByName = () => {
        filteredSalesData.value.sort((a, b) => a.seller.localeCompare(b.seller));
      };
  
      // Ordenar por total (de mayor a menor)
      const sortByTotal = () => {
        filteredSalesData.value.sort((a, b) => b.total - a.total);
      };
  
      // Formatear moneda
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      // Exportar a Excel
      const exportToExcel = () => {
        const exportData = filteredSalesData.value.map(row => {
          const rowData = { Asesor: row.seller };
          filteredPdvs.value.forEach(pdv => {
            rowData[pdv] = row[pdv];
          });
          rowData['Total'] = row.total;
          return rowData;
        });
  
        if (filteredSalesData.value.length > 0) {
          const totalRow = { Asesor: filteredTotals.value.seller };
          filteredPdvs.value.forEach(pdv => {
            totalRow[pdv] = filteredTotals.value[pdv];
          });
          totalRow['Total'] = filteredTotals.value.total;
          exportData.push(totalRow);
        }
  
        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Ventas por Asesor');
        const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/octet-stream' });
        saveAs(blob, `Ventas_por_Asesor_${months.value[month.value - 1].name}_${year.value}.xlsx`);
      };
  
      // Datos para el gráfico de barras horizontales (Top 10 asesores más vendidos)
      const horizontalBarChartData = computed(() => {
        const topSellers = [...filteredSalesData.value]
          .sort((a, b) => b.total - a.total)
          .slice(0, 10);
  
        const labels = topSellers.map(row => row.seller);
        const data = topSellers.map(row => row.total);
  
        const chartData = {
          labels: labels,
          datasets: [
            {
              label: 'Ventas (COP)',
              data: data,
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1
            }
          ]
        };
        console.log('horizontalBarChartData:', chartData);
        return chartData;
      });
  
      const horizontalBarChartOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Ventas (COP)'
            },
            ticks: {
              callback: function(value) {
                return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          y: {
            title: {
              display: true,
              text: 'Asesor'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed.x);
                return label;
              }
            }
          }
        }
      };
  
      // Datos para el gráfico de dona (distribución por asesor, Top 10)
      const doughnutChartData = computed(() => {
        const topSellers = [...filteredSalesData.value]
          .sort((a, b) => b.total - a.total)
          .slice(0, 10);
  
        const colors = [
          'rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)', 'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)', 'rgba(153, 102, 255, 0.6)', 'rgba(255, 159, 64, 0.6)',
          'rgba(255, 99, 132, 0.4)', 'rgba(54, 162, 235, 0.4)', 'rgba(75, 192, 192, 0.4)',
          'rgba(255, 206, 86, 0.4)'
        ];
        const borderColors = colors.map(color => color.replace('0.6', '1').replace('0.4', '1'));
  
        const data = {
          labels: topSellers.map(row => row.seller),
          datasets: [
            {
              label: 'Distribución de Ventas',
              data: topSellers.map(row => row.total),
              backgroundColor: colors,
              borderColor: borderColors,
              borderWidth: 1
            }
          ]
        };
        console.log('doughnutChartData:', data);
        return data;
      });
  
      const doughnutChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed);
                return label;
              }
            }
          }
        }
      };
  
      // Datos para el gráfico de barras: Desglose de Ventas por PDV para el Asesor Seleccionado
      const pdvBreakdownChartData = computed(() => {
        if (!selectedSeller.value) return { labels: [], datasets: [] };
  
        const selectedSellerData = salesData.value.find(row => row.seller === selectedSeller.value);
        if (!selectedSellerData) return { labels: [], datasets: [] };
  
        const labels = filteredPdvs.value.filter(pdv => selectedSellerData[pdv] > 0);
        const data = labels.map(pdv => selectedSellerData[pdv]);
  
        const chartData = {
          labels: labels,
          datasets: [
            {
              label: 'Ventas (COP)',
              data: data,
              backgroundColor: 'rgba(255, 159, 64, 0.6)',
              borderColor: 'rgba(255, 159, 64, 1)',
              borderWidth: 1
            }
          ]
        };
        console.log('pdvBreakdownChartData:', chartData);
        return chartData;
      });
  
      const pdvBreakdownChartOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Ventas (COP)'
            },
            ticks: {
              callback: function(value) {
                return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          y: {
            title: {
              display: true,
              text: 'PDV'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed.x);
                return label;
              }
            }
          }
        }
      };
  
      // Cargar años disponibles al montar el componente
      onMounted(() => {
        fetchAvailableYears();
      });
  
      return {
        year,
        years,
        month,
        months,
        status,
        salesData,
        filteredSalesData,
        pdvs,
        filteredPdvs,
        sellers,
        filteredSellers,
        totals,
        filteredTotals,
        selectedSeller,
        selectedPdv,
        noData,
        horizontalBarChartData,
        horizontalBarChartOptions,
        doughnutChartData,
        doughnutChartOptions,
        pdvBreakdownChartData,
        pdvBreakdownChartOptions,
        fetchData,
        applyFilters,
        sortByName,
        sortByTotal,
        formatCurrency,
        exportToExcel
      };
    }
  };
  </script>
  
  <style scoped>
  .sales-by-seller {
    padding: 20px;
  }
  .filters {
    margin-bottom: 20px;
  }
  label {
    margin-right: 10px;
  }
  select {
    padding: 5px;
  }
  .sort-buttons {
    margin-bottom: 20px;
  }
  .sort-buttons button {
    margin-right: 10px;
    padding: 5px 10px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .sort-buttons button:hover {
    background-color: #2c3e50;
  }
  .sort-buttons button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  .table-container {
    max-width: 100%;
    overflow-x: auto;
  }
  .sales-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .sales-table th, .sales-table td {
    border: 1px solid #ddd;
    padding: 4px;
    text-align: center;
  }
  .sales-table th {
    background-color: #f2f2f2;
    font-size: 11px;
  }
  .sales-table td {
    max-width: 120px;
    white-space: nowrap;
  }
  .sales-table td:first-child {
    max-width: 200px;
    white-space: normal;
    word-wrap: break-word;
    text-align: left;
  }
  .total-row {
    font-weight: bold;
    background-color: #f9f9f9;
  }
  .no-data-message {
    text-align: center;
    color: #888;
    margin: 20px 0;
    font-size: 14px;
  }
  .charts-container {
    margin-top: 40px;
  }
  .chart-wrapper {
    margin-bottom: 60px;
    height: 500px;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
  }
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  </style>