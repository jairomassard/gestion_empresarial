<template>
    <div class="daily-profit">
      <h1>Utilidad Diaria por PDV - {{ months[month - 1].name }} {{ year }}</h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="updateDaysAndFetch">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <label>Mes:</label>
        <select v-model="month" @change="updateDaysAndFetch">
          <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
        </select>
        <label>Estatus PDV:</label>
        <select v-model="status" @change="fetchData">
          <option value="Todos">Todos</option>
          <option value="Activo">Activo</option>
          <option value="Inactivo">Inactivo</option>
        </select>
        <label>PDV:</label>
        <select v-model="selectedPDV" @change="fetchData">
          <option value="Todos">Todos</option>
          <option v-for="pdv in pdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
        </select>
        <label>Día:</label>
        <select v-model="selectedDay" @change="fetchData">
          <option value="Todos">Todos</option>
          <option v-for="day in daysInMonth" :key="day" :value="day">{{ day }}</option>
        </select>
      </div>
  
      <div class="actions">
        <button @click="exportToExcel">Exportar a Excel</button>
        <button @click="downloadChart('barChart')">Descargar Gráfico de Utilidad por PDV</button>
        <button @click="downloadChart('lineChart')">Descargar Gráfico de Tendencia</button>
      </div>
  
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes, año, día y filtros seleccionados.
      </div>
  
      <div v-if="!noData" class="charts-container">
        <div class="chart-wrapper">
          <h2>Utilidad Total por PDV</h2>
          <Bar id="barChart" :data="barChartData" :options="barChartOptions" />
        </div>
  
        <div class="chart-wrapper">
          <h2>Tendencia de Utilidad Diaria</h2>
          <div class="pdv-selector">
            <label>Seleccionar PDV:</label>
            <select v-model="selectedPdv">
              <option value="total">Total (Todos los PDVs)</option>
              <option v-for="pdv in filteredPdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
            </select>
          </div>
          <Line id="lineChart" :data="lineChartData" :options="lineChartOptions" />
        </div>
      </div>
  
      <div v-if="!noData" class="table-container">
        <table class="profit-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th v-for="pdv in filteredPdvs" :key="pdv" colspan="4">{{ pdv }}</th>
              <th colspan="4">Total</th>
            </tr>
            <tr>
              <th></th>
              <th v-for="pdv in filteredPdvs" :key="pdv + '-ventas'">Ventas</th>
              <th v-for="pdv in filteredPdvs" :key="pdv + '-costos'">Costos</th>
              <th v-for="pdv in filteredPdvs" :key="pdv + '-produccion'">Producción</th>
              <th v-for="pdv in filteredPdvs" :key="pdv + '-utilidad'">Utilidad</th>
              <th>Ventas</th>
              <th>Costos</th>
              <th>Producción</th>
              <th>Utilidad</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredDailyProfitData" :key="row.date">
              <td>{{ row.date }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-ventas'">{{ formatCurrency(row[pdv].ventas) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-costos'">{{ formatCurrency(row[pdv].costos) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-produccion'">{{ formatCurrency(row[pdv].produccion) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-utilidad'">{{ formatCurrency(row[pdv].utilidad) }}</td>
              <td>{{ formatCurrency(row.total.ventas) }}</td>
              <td>{{ formatCurrency(row.total.costos) }}</td>
              <td>{{ formatCurrency(row.total.produccion) }}</td>
              <td>{{ formatCurrency(row.total.utilidad) }}</td>
            </tr>
            <tr class="total-row" v-if="filteredDailyProfitData.length > 0">
              <td>{{ filteredTotals.date }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-ventas'">{{ formatCurrency(filteredTotals[pdv].ventas) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-costos'">{{ formatCurrency(filteredTotals[pdv].costos) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-produccion'">{{ formatCurrency(filteredTotals[pdv].produccion) }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv + '-utilidad'">{{ formatCurrency(filteredTotals[pdv].utilidad) }}</td>
              <td>{{ formatCurrency(filteredTotals.total.ventas) }}</td>
              <td>{{ formatCurrency(filteredTotals.total.costos) }}</td>
              <td>{{ formatCurrency(filteredTotals.total.produccion) }}</td>
              <td>{{ formatCurrency(filteredTotals.total.utilidad) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed, watch } from 'vue';
  import { useStore } from 'vuex';
  import { useRouter } from 'vue-router';
  import axios from '@/api/axios';
  import { Bar, Line } from 'vue-chartjs';
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    BarElement,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    TimeScale
  } from 'chart.js';
  import ChartDataLabels from 'chartjs-plugin-datalabels';
  import * as XLSX from 'xlsx';
  import html2canvas from 'html2canvas';
  import 'chartjs-adapter-date-fns';
  
  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    BarElement,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    TimeScale,
    ChartDataLabels
  );
  
  export default {
    name: 'DailyProfit',
    components: { Bar, Line },
    setup() {
      const store = useStore();
      const router = useRouter();
  
      // Datos reactivos
      const year = ref(null);
      const years = ref([]);
      const currentDate = new Date();
      const currentMonth = currentDate.getMonth() + 1;
      const currentYear = currentDate.getFullYear();
      const month = ref(currentMonth);
      const status = ref('Activo');
      const selectedPDV = ref('Todos');
      const selectedDay = ref('Todos');
      const daysInMonth = ref([]);
      const dailyProfitData = ref([]);
      const filteredDailyProfitData = ref([]);
      const pdvs = ref([]);
      const filteredPdvs = ref([]);
      const totals = ref({});
      const filteredTotals = ref({});
      const selectedPdv = ref('total');
  
      const months = ref([
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ]);
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        return filteredDailyProfitData.value.length === 0 ||
               filteredDailyProfitData.value.every(row => row.total.utilidad === 0);
      });
  
      // Generar lista de días del mes
      const updateDaysInMonth = () => {
        if (!year.value || !month.value) return;
        const daysInMonthMap = {
          1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
          7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        };
        if (month.value === 2 && year.value % 4 === 0 && (year.value % 100 !== 0 || year.value % 400 === 0)) {
          daysInMonthMap[2] = 29;
        }
        const numDays = daysInMonthMap[month.value] || 30;
        daysInMonth.value = Array.from({ length: numDays }, (_, i) => i + 1);
        selectedDay.value = 'Todos';
      };
  
      // Obtener años disponibles
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            updateDaysInMonth();
            fetchPdvs();
            fetchData();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          updateDaysInMonth();
          if (error.response && error.response.status === 401) {
            router.push('/login');
          } else {
            fetchPdvs();
            fetchData();
          }
        }
      };
  
      // Obtener lista de PDVs
      const fetchPdvs = async () => {
        try {
          const params = { year: year.value, month: month.value, status: status.value };
          if (selectedDay.value !== 'Todos') params.day = selectedDay.value;
          const response = await axios.get('/dashboard/product-profit', { params });
          const data = response.data.data || [];
          const pdvSet = new Set();
          data.forEach(row => {
            Object.keys(row.almacenes || {}).forEach(pdv => pdvSet.add(pdv));
          });
          pdvs.value = Array.from(pdvSet).sort();
        } catch (error) {
          console.error('Error fetching PDVs:', error);
          pdvs.value = [];
        }
      };
  
      // Obtener datos de utilidad
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const params = { year: year.value, month: month.value, status: status.value };
          if (selectedPDV.value !== 'Todos') params.pdv = selectedPDV.value;
          if (selectedDay.value !== 'Todos') params.day = selectedDay.value;
          const response = await axios.get('/dashboard/product-profit', { params });
          const rawData = response.data.data || [];
  
          // Agrupar datos por día y PDV
          const dataByDay = {};
          const daysInMonthMap = {
            1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
          };
          if (month.value === 2 && year.value % 4 === 0 && (year.value % 100 !== 0 || year.value % 400 === 0)) {
            daysInMonthMap[2] = 29;
          }
          const numDays = daysInMonthMap[month.value] || 30;
  
          // Inicializar datos para cada día
          for (let day = 1; day <= numDays; day++) {
            const date = new Date(year.value, month.value - 1, day);
            const dayName = date.toLocaleDateString('es-ES', { weekday: 'long' });
            const formattedDate = `${dayName}, ${day.toString().padStart(2, '0')}/${month.value.toString().padStart(2, '0')}/${year.value}`;
            dataByDay[day] = {
              date: formattedDate,
              pdvs: {},
              total: { ventas: 0, costos: 0, produccion: 0, utilidad: 0 }
            };
            pdvs.value.forEach(pdv => {
              dataByDay[day].pdvs[pdv] = { ventas: 0, costos: 0, produccion: 0, utilidad: 0 };
            });
          }
  
          // Procesar datos del endpoint
          rawData.forEach(row => {
            const almacenes = row.almacenes || {};
            Object.entries(almacenes).forEach(([pdv, pdvData]) => {
              // Asumir que los datos son del día especificado o distribuir uniformemente
              const dayKey = selectedDay.value !== 'Todos' ? parseInt(selectedDay.value) : 1;
              if (dataByDay[dayKey]) {
                dataByDay[dayKey].pdvs[pdv] = dataByDay[dayKey].pdvs[pdv] || {
                  ventas: 0, costos: 0, produccion: 0, utilidad: 0
                };
                dataByDay[dayKey].pdvs[pdv].ventas += pdvData.venta || 0;
                dataByDay[dayKey].pdvs[pdv].costos += (row.costos * (pdvData.cantidad_vendida / row.cantidad_vendida)) || 0;
                dataByDay[dayKey].pdvs[pdv].produccion += (row.produccion * (pdvData.cantidad_vendida / row.cantidad_vendida)) || 0;
                dataByDay[dayKey].pdvs[pdv].utilidad += (row.utilidad * (pdvData.cantidad_vendida / row.cantidad_vendida)) || 0;
              }
            });
          });
  
          // Calcular totales por día
          Object.values(dataByDay).forEach(dayData => {
            Object.entries(dayData.pdvs).forEach(([pdv, metrics]) => {
              dayData.total.ventas += metrics.ventas;
              dayData.total.costos += metrics.costos;
              dayData.total.produccion += metrics.produccion;
              dayData.total.utilidad += metrics.utilidad;
            });
          });
  
          dailyProfitData.value = Object.values(dataByDay).filter(dayData => dayData.total.utilidad > 0 || selectedDay.value !== 'Todos');
          updateFilteredData();
        } catch (error) {
          console.error('Error fetching daily profit data:', error);
          dailyProfitData.value = [];
          filteredDailyProfitData.value = [];
          filteredPdvs.value = [];
          filteredTotals.value = {};
          if (error.response && error.response.status === 401) {
            router.push('/login');
          }
        }
      };
  
      // Actualizar datos filtrados
      const updateFilteredData = () => {
        // Filtrar PDVs
        if (selectedPDV.value === 'Todos') {
          filteredPdvs.value = pdvs.value;
        } else {
          filteredPdvs.value = pdvs.value.filter(pdv => pdv === selectedPDV.value);
        }
  
        // Filtrar días
        if (selectedDay.value === 'Todos') {
          filteredDailyProfitData.value = dailyProfitData.value;
        } else {
          const dayStr = selectedDay.value.toString().padStart(2, '0');
          const monthStr = month.value.toString().padStart(2, '0');
          const datePattern = `${dayStr}/${monthStr}/${year.value}`;
          filteredDailyProfitData.value = dailyProfitData.value.filter(row => row.date.includes(datePattern));
        }
  
        // Calcular totales
        filteredTotals.value = { date: 'TOTALES' };
        filteredPdvs.value.forEach(pdv => {
          filteredTotals.value[pdv] = {
            ventas: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.pdvs[pdv]?.ventas || 0), 0),
            costos: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.pdvs[pdv]?.costos || 0), 0),
            produccion: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.pdvs[pdv]?.produccion || 0), 0),
            utilidad: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.pdvs[pdv]?.utilidad || 0), 0)
          };
        });
        filteredTotals.value.total = {
          ventas: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.ventas || 0), 0),
          costos: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.costos || 0), 0),
          produccion: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.produccion || 0), 0),
          utilidad: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.utilidad || 0), 0)
        };
      };
  
      // Actualizar días y obtener datos
      const updateDaysAndFetch = () => {
        updateDaysInMonth();
        fetchPdvs();
        fetchData();
      };
  
      // Formatear moneda
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      // Gráfico de barras: Utilidad Total por PDV
      const barChartData = computed(() => ({
        labels: filteredPdvs.value,
        datasets: [
          {
            label: 'Utilidad Total (COP)',
            data: filteredPdvs.value.map(pdv => filteredTotals.value[pdv]?.utilidad || 0),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
          }
        ]
      }));
  
      const barChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Utilidad (COP)' },
            ticks: {
              callback: function(value) {
                return formatCurrency(value);
              }
            }
          },
          x: {
            title: { display: true, text: 'Punto de Venta' }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
              }
            }
          },
          datalabels: {
            display: true,
            anchor: 'center',
            align: 'center',
            color: '#fff',
            font: { size: 13, weight: 'bold' },
            formatter: function(value) {
              return formatCurrency(value);
            }
          }
        }
      };
  
      // Gráfico de líneas: Tendencia de Utilidad Diaria
      const lineChartData = computed(() => {
        const labels = filteredDailyProfitData.value.map(row => {
          const dateStr = row.date.split(', ')[1];
          const [day, month, year] = dateStr.split('/');
          return `${year}-${month}-${day}`;
        });
  
        let data;
        if (selectedPdv.value === 'total') {
          data = filteredDailyProfitData.value.map(row => row.total.utilidad);
        } else {
          data = filteredDailyProfitData.value.map(row => row.pdvs[selectedPdv.value]?.utilidad || 0);
        }
  
        return {
          labels: labels,
          datasets: [
            {
              label: selectedPdv.value === 'total' ? 'Utilidad Total (COP)' : `Utilidad de ${selectedPdv.value} (COP)`,
              data: data,
              fill: false,
              borderColor: 'rgba(75, 192, 192, 1)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              tension: 0.1
            }
          ]
        };
      });
  
      const lineChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              tooltipFormat: 'dd/MM/yyyy',
              displayFormats: { day: 'dd/MM/yyyy' }
            },
            title: { display: true, text: 'Fecha' }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Utilidad (COP)' },
            ticks: {
              callback: function(value) {
                return formatCurrency(value);
              }
            }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
              }
            }
          },
          datalabels: { display: false }
        }
      };
  
      // Exportar a Excel
      const exportToExcel = () => {
        const data = filteredDailyProfitData.value.map(row => {
          const rowData = { Fecha: row.date };
          filteredPdvs.value.forEach(pdv => {
            rowData[`${pdv} - Ventas`] = row.pdvs[pdv].ventas;
            rowData[`${pdv} - Costos`] = row.pdvs[pdv].costos;
            rowData[`${pdv} - Producción`] = row.pdvs[pdv].produccion;
            rowData[`${pdv} - Utilidad`] = row.pdvs[pdv].utilidad;
          });
          rowData['Total - Ventas'] = row.total.ventas;
          rowData['Total - Costos'] = row.total.costos;
          rowData['Total - Producción'] = row.total.produccion;
          rowData['Total - Utilidad'] = row.total.utilidad;
          return rowData;
        });
  
        data.push({
          Fecha: filteredTotals.value.date,
          ...Object.fromEntries(
            filteredPdvs.value.flatMap(pdv => [
              [`${pdv} - Ventas`, filteredTotals.value[pdv].ventas],
              [`${pdv} - Costos`, filteredTotals.value[pdv].costos],
              [`${pdv} - Producción`, filteredTotals.value[pdv].produccion],
              [`${pdv} - Utilidad`, filteredTotals.value[pdv].utilidad]
            ])
          ),
          'Total - Ventas': filteredTotals.value.total.ventas,
          'Total - Costos': filteredTotals.value.total.costos,
          'Total - Producción': filteredTotals.value.total.produccion,
          'Total - Utilidad': filteredTotals.value.total.utilidad
        });
  
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Utilidad Diaria');
        XLSX.writeFile(wb, `Utilidad_Diaria_${year.value}_${month.value}${selectedDay.value !== 'Todos' ? `_Dia${selectedDay.value}` : ''}.xlsx`);
      };
  
      // Descargar gráficos
      const downloadChart = async (chartId) => {
        const canvas = document.getElementById(chartId);
        const link = document.createElement('a');
        link.href = await html2canvas(canvas).then(canvas => canvas.toDataURL('image/png'));
        link.download = `${chartId}_${year.value}_${month.value}${selectedDay.value !== 'Todos' ? `_Dia${selectedDay.value}` : ''}.png`;
        link.click();
      };
  
      // Cargar años disponibles
      onMounted(() => {
        if (store.state.auth.token) {
          fetchAvailableYears();
        } else {
          router.push('/login');
        }
      });
  
      watch(selectedPdv, () => {
        console.log('PDV seleccionado cambiado a:', selectedPdv.value);
      });
  
      return {
        year,
        years,
        month,
        months,
        status,
        selectedPDV,
        selectedDay,
        daysInMonth,
        dailyProfitData,
        filteredDailyProfitData,
        pdvs,
        filteredPdvs,
        totals,
        filteredTotals,
        noData,
        selectedPdv,
        barChartData,
        barChartOptions,
        lineChartData,
        lineChartOptions,
        fetchData,
        updateDaysAndFetch,
        formatCurrency,
        exportToExcel,
        downloadChart
      };
    }
  };
  </script>
  
  <style scoped>
  .daily-profit {
    padding: 20px;
  }
  
  .filters {
    margin-bottom: 20px;
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .actions {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
  }
  
  .actions button {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .actions button:hover {
    background-color: #45a049;
  }
  
  label {
    margin-right: 10px;
    font-weight: bold;
  }
  
  select {
    padding: 5px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
  
  .table-container {
    max-width: 100%;
    overflow-x: auto;
    margin-top: 40px;
  }
  
  .profit-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  
  .profit-table th,
  .profit-table td {
    border: 1px solid #ddd;
    padding: 4px;
    text-align: center;
  }
  
  .profit-table th {
    background-color: #f2f2f2;
    font-size: 11px;
  }
  
  .profit-table td {
    max-width: 120px;
    white-space: nowrap;
  }
  
  .profit-table td:first-child {
    font-size: 10px;
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
    margin-bottom: 40px;
  }
  
  .chart-wrapper {
    margin-bottom: 60px;
    height: 400px;
  }
  
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .pdv-selector {
    margin-bottom: 20px;
    text-align: center;
  }
  </style>