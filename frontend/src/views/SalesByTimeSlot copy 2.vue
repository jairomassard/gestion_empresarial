<template>
    <div class="sales-by-time-slot">
      <h1>Ventas por Franja del Día - {{ months[month - 1].name }} {{ year }}</h1>
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
              <th>PDV</th>
              <th>Mañana</th>
              <th>% Part</th>
              <th>Tarde</th>
              <th>% Part</th>
              <th>Noche</th>
              <th>% Part</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in salesData" :key="row.pdv">
              <td>{{ row.pdv }}</td>
              <td>{{ formatCurrency(row.morning_sales) }}</td>
              <td>{{ row.morning_part }}%</td>
              <td>{{ formatCurrency(row.afternoon_sales) }}</td>
              <td>{{ row.afternoon_part }}%</td>
              <td>{{ formatCurrency(row.night_sales) }}</td>
              <td>{{ row.night_part }}%</td>
              <td>{{ formatCurrency(row.total) }}</td>
            </tr>
            <tr class="total-row" v-if="salesData.length > 0">
              <td>{{ totals.pdv }}</td>
              <td>{{ formatCurrency(totals.morning_sales) }}</td>
              <td>{{ totals.morning_part }}%</td>
              <td>{{ formatCurrency(totals.afternoon_sales) }}</td>
              <td>{{ totals.afternoon_part }}%</td>
              <td>{{ formatCurrency(totals.night_sales) }}</td>
              <td>{{ totals.night_part }}%</td>
              <td>{{ formatCurrency(totals.total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Gráficos -->
      <div v-if="!noData" class="charts-container">
        <!-- Gráfico de Barras Apiladas: Ventas por Franja del Día por PDV -->
        <div class="chart-wrapper">
          <h2>Ventas por Franja del Día por PDV</h2>
          <Bar :data="stackedBarChartData" :options="stackedBarChartOptions" />
        </div>
  
        <!-- Gráfico de Pastel: Distribución de Ventas por Franja -->
        <div class="chart-wrapper">
          <h2>Distribución de Ventas por Franja</h2>
          <Pie :data="pieChartData" :options="pieChartOptions" />
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed, watch } from 'vue';
  import axios from '@/api/axios';
  import { Bar, Pie } from 'vue-chartjs';
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
    name: 'SalesByTimeSlot',
    components: {
      Bar,
      Pie
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
      const pdvs = ref([]);
      const totals = ref({});
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        const result = salesData.value.length > 0 && salesData.value.every(row => row.total === 0);
        console.log('noData:', result, 'salesData:', salesData.value);
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
  
      // Obtener datos de ventas por franja del día
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const response = await axios.get('/dashboard/sales-by-time-slot', {
            params: { year: year.value, month: month.value, status: status.value }
          });
          salesData.value = response.data.data || [];
          pdvs.value = response.data.pdvs || [];
          totals.value = response.data.totals || {};
          console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, totals: totals.value });
        } catch (error) {
          console.error('Error fetching sales by time slot data:', error);
          salesData.value = [];
          pdvs.value = [];
          totals.value = {};
        }
      };
  
      // Formatear moneda
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      // Datos para el gráfico de barras apiladas
      const stackedBarChartData = computed(() => {
        const data = {
          labels: pdvs.value,
          datasets: [
            {
              label: 'Mañana',
              data: salesData.value.map(row => row.morning_sales),
              backgroundColor: 'rgba(255, 99, 132, 0.6)',
              borderColor: 'rgba(255, 99, 132, 1)',
              borderWidth: 1,
              stack: 'Stack 0'
            },
            {
              label: 'Tarde',
              data: salesData.value.map(row => row.afternoon_sales),
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1,
              stack: 'Stack 0'
            },
            {
              label: 'Noche',
              data: salesData.value.map(row => row.night_sales),
              backgroundColor: 'rgba(75, 192, 192, 0.6)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1,
              stack: 'Stack 0'
            }
          ]
        };
        console.log('stackedBarChartData:', data);
        return data;
      });
  
      const stackedBarChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Punto de Venta'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Ventas (COP)'
            },
            ticks: {
              callback: function(value) {
                return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            },
            stacked: true
          }
        },
        plugins: {
          legend: {
            display: true
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed.y);
                return label;
              }
            }
          }
        }
      };
  
      // Datos para el gráfico de pastel (distribución por franja)
      const pieChartData = computed(() => {
        const data = {
          labels: ['Mañana', 'Tarde', 'Noche'],
          datasets: [
            {
              label: 'Distribución de Ventas',
              data: [
                totals.value.morning_sales || 0,
                totals.value.afternoon_sales || 0,
                totals.value.night_sales || 0
              ],
              backgroundColor: [
                'rgba(255, 99, 132, 0.6)',
                'rgba(54, 162, 235, 0.6)',
                'rgba(75, 192, 192, 0.6)'
              ],
              borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(75, 192, 192, 1)'
              ],
              borderWidth: 1
            }
          ]
        };
        console.log('pieChartData:', data);
        return data;
      });
  
      const pieChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
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
        pdvs,
        totals,
        noData,
        stackedBarChartData,
        stackedBarChartOptions,
        pieChartData,
        pieChartOptions,
        fetchData,
        formatCurrency
      };
    }
  };
  </script>
  
  <style scoped>
  .sales-by-time-slot {
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
    margin-bottom: 60px; /* Aumentamos el espacio entre gráficos */
    height: 300px; /* Reducimos la altura de los gráficos */
    max-width: 800px; /* Limitamos el ancho máximo */
    margin-left: auto; /* Centramos horizontalmente */
    margin-right: auto;
  }
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  </style>
