<template>
  <div class="sales-by-seller">
    <h1>
      Ventas por Asesor - {{ months[month - 1].name }}
      <span v-if="day"> {{ day }} </span>
      {{ year }}
    </h1>
    <div class="filters">
      <label>Año:</label>
      <select v-model="year" @change="updateDaysAndFetchData">
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </select>
      <label>Mes:</label>
      <select v-model="month" @change="updateDaysAndFetchData">
        <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
      </select>
      <label>Día:</label>
      <select v-model="day" @change="fetchData">
        <option :value="null">Todo el mes</option>
        <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
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
      No hay datos disponibles para el mes, año y día seleccionados.
    </div>

    <!-- Contenedor para gráficos y tabla -->
    <div v-else>
      <!-- Gráficos -->
      <div class="charts-container">
        <!-- Gráfico de Barras Horizontales: Top 10 Asesores Más Vendidos -->
        <div class="chart-wrapper top-bar-chart">
          <h2>Top 10 Asesores con más ventas</h2>
          <Bar :data="horizontalBarChartData" :options="horizontalBarChartOptions" />
        </div>

        <!-- Gráfico de Barras: Desglose de Ventas por PDV para el Asesor Seleccionado -->
        <div v-if="selectedSeller" class="chart-wrapper pdv-breakdown-chart">
          <h2>Ventas por PDV - {{ selectedSeller }}</h2>
          <Bar :data="pdvBreakdownChartData" :options="pdvBreakdownChartOptions" />
        </div>
      </div>

      <!-- Tabla -->
      <div class="table-container">
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
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from '@/api/axios';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { Bar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import ChartDataLabels from 'chartjs-plugin-datalabels';

// Registrar los componentes de Chart.js
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ChartDataLabels
);

export default {
  name: 'SalesBySeller',
  components: {
    Bar
  },
  setup() {
    // Datos reactivos
    const store = useStore();
    const router = useRouter();
    const year = ref(null);
    const years = ref([]);
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1;
    const currentYear = currentDate.getFullYear();
    const month = ref(currentMonth);
    const months = ref([
      { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
      { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
      { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
      { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
    ]);
    const day = ref(null);
    const days = ref([]);
    const status = ref('Activo');
    const salesData = ref([]);
    const filteredSalesData = ref([]);
    const pdvs = ref([]);
    const sellers = ref([]);
    const totals = ref({});
    const selectedSeller = ref('');
    const selectedPdv = ref('');

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = filteredSalesData.value.length > 0 && filteredSalesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'filteredSalesData:', filteredSalesData.value);
      return result;
    });

    // Computed para PDVs filtrados
    const filteredPdvs = computed(() => {
      if (selectedPdv.value) {
        return pdvs.value.filter(pdv => pdv === selectedPdv.value);
      }
      return pdvs.value;
    });

    // Computed para asesores filtrados
    const filteredSellers = computed(() => {
      if (selectedPdv.value) {
        return sellers.value.filter(seller => {
          const sellerData = salesData.value.find(row => row.seller === seller);
          return sellerData && sellerData[selectedPdv.value] > 0;
        });
      }
      return sellers.value;
    });

    // Computed para totales filtrados
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
          updateDays();
          fetchData();
        }
      } catch (error) {
        console.error('Error fetching available years:', error);
        years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
        year.value = currentYear;
        updateDays();
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en available-years, redirigiendo al login');
          router.push('/login');
        } else {
          fetchData();
        }
      }
    };

    // Actualizar la lista de días disponibles según el año y mes seleccionados
    const updateDays = () => {
      if (!year.value || !month.value) return;
      const daysInMonth = new Date(year.value, month.value, 0).getDate();
      days.value = Array.from({ length: daysInMonth }, (_, i) => i + 1);
      if (day.value && day.value > daysInMonth) {
        day.value = null;
      }
    };

    // Combinar updateDays y fetchData para cuando cambien año o mes
    const updateDaysAndFetchData = () => {
      updateDays();
      fetchData();
    };

    // Obtener datos de ventas por asesor
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const response = await axios.get('/dashboard/sales-by-seller', {
          params: { year: year.value, month: month.value, day: day.value, status: status.value }
        });
        salesData.value = response.data.data || [];
        pdvs.value = response.data.pdvs || [];
        sellers.value = response.data.sellers || [];
        totals.value = response.data.totals || {};
        applyFilters();
        console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, sellers: sellers.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching sales by seller data:', error);
        salesData.value = [];
        filteredSalesData.value = [];
        pdvs.value = [];
        sellers.value = [];
        totals.value = {};
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Aplicar filtros combinados (PDV y Asesor)
    const applyFilters = () => {
      let filtered = [...salesData.value];

      if (selectedPdv.value) {
        filtered = filtered.filter(row => row[selectedPdv.value] > 0);
      }

      if (selectedSeller.value) {
        filtered = filtered.filter(row => row.seller === selectedSeller.value);
      }

      filteredSalesData.value = filtered;
      sortByTotal();
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
      saveAs(blob, `Ventas_por_Asesor_${months.value[month.value - 1].name}_${year.value}${day.value ? `_${day.value}` : ''}.xlsx`);
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
        },
        datalabels: {
          display: true,  // en false no se muestra
          anchor: 'center', // Posicionar la etiqueta en el centro de la barra
          align: 'center', // Alinear el texto al centro
          color: '#fff', // Color del texto (negro para que contraste con el fondo de la barra.  Clanco es #fff)
          font: {
            size: 10,
            weight: 'bold',
          },
          formatter: function (value) {
            return new Intl.NumberFormat('es-CO', {
              style: 'currency',
              currency: 'COP',
              minimumFractionDigits: 0,
            }).format(value);
          },
        },
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
      if (store.state.auth.token) {
        fetchAvailableYears();
      } else {
        console.log('No hay token, redirigiendo al login');
        router.push('/login');
      }
    });

    return {
      year,
      years,
      month,
      months,
      day,
      days,
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
      pdvBreakdownChartData,
      pdvBreakdownChartOptions,
      fetchData,
      updateDaysAndFetchData,
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
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters label {
  font-weight: bold;
}

.filters select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ccc;
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
  /* Ajusta la separación entre los gráficos y la tabla aquí */
  margin-top: 120px; /* Cambia este valor para aumentar o disminuir la separación */
}

.sales-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.sales-table th,
.sales-table td {
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
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  max-width: 1400px;
  margin: 0 auto;
  margin-bottom: 20px;
}

.chart-wrapper {
  /* Ajusta la altura de los gráficos aquí */
  height: 400px; /* Cambia este valor para aumentar o disminuir la altura */
}

/* Gráfico de barras horizontales (Top 10 Asesores Más Vendidos) */
.chart-wrapper.top-bar-chart {
  flex: 1;
  /* Ajusta el ancho del gráfico de "Top 10 Asesores Más Vendidos" aquí */
  min-width: 500px; /* Ancho mínimo */
  max-width: 1200px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
}

/* Gráfico de barras (Desglose de Ventas por PDV) */
.chart-wrapper.pdv-breakdown-chart {
  flex: 1;
  /* Ajusta el ancho del gráfico de "Ventas por PDV" aquí */
  min-width: 500px; /* Ancho mínimo */
  max-width: 1200px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
}

.chart-wrapper h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>