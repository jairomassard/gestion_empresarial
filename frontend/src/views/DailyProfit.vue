<template>
    <div class="daily-profit">
      <h1>Utilidad Diaria por PDV - {{ monthName }} {{ year }}</h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="fetchData">
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
  
      <!-- Mensaje si no hay datos -->
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes, año y filtros seleccionados.
      </div>
  
      <!-- Gráficos -->
      <div v-if="!noData" class="charts-container">
        <!-- Gráfico de Barras: Utilidad Total por PDV -->
        <div class="chart-wrapper">
          <h2>Utilidad Total por PDV</h2>
          <Bar :data="barChartData" :options="barChartOptions" />
        </div>
  
        <!-- Gráfico de Líneas: Tendencia de Utilidad Diaria -->
        <div class="chart-wrapper">
          <h2>Tendencia de Utilidad Diaria</h2>
          <div class="pdv-selector">
            <label>Seleccionar PDV:</label>
            <select v-model="selectedPdv">
              <option value="total">Total (Todos los PDVs)</option>
              <option v-for="pdv in filteredPdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
            </select>
          </div>
          <Line :data="lineChartData" :options="lineChartOptions" />
        </div>
      </div>
  
      <!-- Tabla -->
      <div v-if="!noData" class="table-container">
        <table class="profit-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th v-for="pdv in filteredPdvs" :key="pdv">{{ pdv }}</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredDailyProfitData" :key="row.date">
              <td>{{ row.date }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv">
                {{ row[pdv] ? formatCurrency(row[pdv].utilidad) : '-' }}
              </td>
              <td>{{ formatCurrency(row.total.utilidad) }}</td>
            </tr>
            <tr class="total-row" v-if="filteredDailyProfitData.length > 0">
              <td>{{ filteredTotals.date }}</td>
              <td v-for="pdv in filteredPdvs" :key="pdv">
                {{ filteredTotals[pdv] ? formatCurrency(filteredTotals[pdv].utilidad) : '-' }}
              </td>
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
  import 'chartjs-adapter-date-fns';
  
  // Registrar los componentes de Chart.js
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
    components: {
      Bar,
      Line
    },
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
      const months = ref([
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ]);
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
  
      // Computed para el nombre del mes
      const monthName = computed(() => {
        const selectedMonth = months.value.find(m => m.num === month.value);
        return selectedMonth ? selectedMonth.name : 'Mes';
      });
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        const result = filteredDailyProfitData.value.length === 0 ||
                      filteredDailyProfitData.value.every(row => !row.total || row.total.utilidad === 0);
        console.log('noData:', result, 'filteredDailyProfitData:', filteredDailyProfitData.value);
        return result;
      });
  
      // Generar lista de días del mes
      const updateDaysInMonth = () => {
        if (!year.value || !month.value) return;
        console.log('Actualizando días para:', { year: year.value, month: month.value });
        const daysInMonthMap = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31};
        if (month.value === 2 && year.value % 4 === 0 && (year.value % 100 !== 0 || year.value % 400 === 0)) {
          daysInMonthMap[2] = 29;
        }
        const numDays = daysInMonthMap[month.value] || 30;
        daysInMonth.value = Array.from({ length: numDays }, (_, i) => i + 1);
        selectedDay.value = 'Todos';
      };
  
      // Actualizar días y obtener datos
      const updateDaysAndFetch = () => {
        updateDaysInMonth();
        fetchData();
      };
  
      // Obtener los años disponibles
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            updateDaysInMonth();
            fetchData();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          updateDaysInMonth();
          fetchData();
        }
      };
  
      // Obtener datos de utilidad diaria
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const params = { year: year.value, month: month.value, status: status.value };
          if (selectedPDV.value !== 'Todos') params.pdv = selectedPDV.value;
          if (selectedDay.value !== 'Todos') params.day = selectedDay.value;
  
          const response = await axios.get('/dashboard/daily-profit', { params });
          dailyProfitData.value = response.data.data || [];
          pdvs.value = response.data.pdvs || [];
          totals.value = response.data.totals || {};
          updateFilteredData();
          console.log('Datos recibidos:', { dailyProfitData: dailyProfitData.value, pdvs: pdvs.value, totals: totals.value });
        } catch (error) {
          console.error('Error fetching daily profit data:', error);
          dailyProfitData.value = [];
          pdvs.value = [];
          totals.value = {};
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
        // Filtrar PDVs con datos
        const pdvsWithData = new Set();
        dailyProfitData.value.forEach(row => {
          Object.keys(row).forEach(key => {
            if (key !== 'date' && key !== 'total' && pdvs.value.includes(key)) {
              pdvsWithData.add(key);
            }
          });
        });
  
        if (selectedPDV.value === 'Todos') {
          filteredPdvs.value = pdvs.value.filter(pdv => pdvsWithData.has(pdv));
        } else {
          filteredPdvs.value = pdvs.value.filter(pdv => pdv === selectedPDV.value && pdvsWithData.has(pdv));
        }
  
        if (selectedDay.value === 'Todos') {
          filteredDailyProfitData.value = dailyProfitData.value;
        } else {
          const dayStr = selectedDay.value.toString().padStart(2, '0');
          const monthStr = month.value.toString().padStart(2, '0');
          const datePattern = `${dayStr}/${monthStr}/${year.value}`;
          filteredDailyProfitData.value = dailyProfitData.value.filter(row => {
            const dateStr = row.date.includes(', ') ? row.date.split(', ')[1] : row.date;
            return dateStr.includes(datePattern);
          });
        }
  
        filteredTotals.value = { date: 'TOTALES' };
        filteredPdvs.value.forEach(pdv => {
          filteredTotals.value[pdv] = {
            ventas: filteredDailyProfitData.value.reduce((sum, row) => sum + (row[pdv]?.ventas || 0), 0),
            costos: filteredDailyProfitData.value.reduce((sum, row) => sum + (row[pdv]?.costos || 0), 0),
            produccion: filteredDailyProfitData.value.reduce((sum, row) => sum + (row[pdv]?.produccion || 0), 0),
            utilidad: filteredDailyProfitData.value.reduce((sum, row) => sum + (row[pdv]?.utilidad || 0), 0)
          };
        });
        filteredTotals.value.total = {
          ventas: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.ventas || 0), 0),
          costos: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.costos || 0), 0),
          produccion: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.produccion || 0), 0),
          utilidad: filteredDailyProfitData.value.reduce((sum, row) => sum + (row.total?.utilidad || 0), 0)
        };
      };
  
      // Formatear moneda
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      // Datos para el gráfico de barras
      const barChartData = computed(() => {
        const data = {
          labels: filteredPdvs.value,
          datasets: [
            {
              label: 'Utilidad Total (COP)',
              data: filteredPdvs.value.map(pdv => filteredTotals.value[pdv]?.utilidad || 0),
              backgroundColor: 'rgba(75, 192, 192, 0.6)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1
            }
          ]
        };
        console.log('barChartData:', data);
        return data;
      });
  
      const barChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Utilidad (COP)'
            },
            ticks: {
              callback: function(value) {
                return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Punto de Venta'
            }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed.y);
                return label;
              }
            }
          },
          datalabels: {
            display: true,
            anchor: 'center',
            align: 'center',
            color: '#fff',
            font: { size: 11, weight: 'bold' },
            formatter: function(value) {
              return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
            }
          }
        }
      };
  
      // Datos para el gráfico de líneas
      const lineChartData = computed(() => {
        const labels = filteredDailyProfitData.value.map(row => {
          const dateStr = row.date.includes(', ') ? row.date.split(', ')[1] : row.date;
          const [day, month, year] = dateStr.split('/');
          return `${year}-${month}-${day}`;
        });
  
        let data;
        if (selectedPdv.value === 'total') {
          data = filteredDailyProfitData.value.map(row => row.total.utilidad);
        } else {
          data = filteredDailyProfitData.value.map(row => (row[selectedPdv.value]?.utilidad || 0));
        }
  
        const chartData = {
          labels: labels,
          datasets: [
            {
              label: selectedPdv.value === 'total' ? 'Utilidad Total (COP)' : `Utilidad de ${selectedPdv.value} (COP)`,
              data: data,
              fill: false,
              borderColor: 'rgba(255, 99, 132, 1)',
              backgroundColor: 'rgba(255, 99, 132, 0.2)',
              tension: 0.1
            }
          ]
        };
        console.log('lineChartData:', chartData);
        return chartData;
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
                return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed.y);
                return label;
              }
            }
          },
          datalabels: { display: false }
        }
      };
  
      // Cargar años al montar el componente
      onMounted(() => {
        console.log('Montando componente, estado inicial:', { month: month.value, months: months.value });
        if (store.state.auth.token) {
          fetchAvailableYears();
        } else {
          router.push('/login');
        }
      });
  
      // Actualizar gráficos al cambiar PDV
      watch(selectedPdv, () => {
        console.log('PDV seleccionado cambiado a:', selectedPdv.value);
      });
  
      // Vigilar cambios en month para depuración
      watch(month, (newMonth) => {
        console.log('Month cambiado a:', newMonth);
      });
  
      return {
        year,
        years,
        month,
        months,
        monthName,
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
        formatCurrency
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