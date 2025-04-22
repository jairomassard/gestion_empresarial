<template>
  <div class="sales-by-time-slot">
    <h1>Ventas por Franja del Día - {{ months[month - 1].name }} {{ year }}</h1>
    <div class="filters">
      <label>Año:</label>
      <select v-model="year" @change="fetchData">
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </select>
      <label>Mes:</label>
      <select v-model="month" @change="updateDaysAndFetch">
        <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
      </select>
      <!-- Filtro por Día -->
      <label>Día:</label>
      <select v-model="selectedDay" @change="fetchData">
        <option value="Todos">Todos</option>
        <option v-for="day in daysInMonth" :key="day" :value="day">{{ day }}</option>
      </select>
      <label>Estatus PDV:</label>
      <select v-model="status" @change="fetchData">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <!-- Filtro por PDV -->
      <label>PDV:</label>
      <select v-model="selectedPDV" @change="fetchData">
        <option value="Todos">Todos</option>
        <option v-for="pdv in pdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
      </select>
      
    </div>

    <!-- Mensaje si no hay datos -->
    <div v-if="noData" class="no-data-message">
      No hay datos disponibles para el mes, año y filtros seleccionados.
    </div>

    <!-- Contenedor para gráficos y tabla -->
    <div v-if="!noData">
      <!-- Gráficos -->
      <div class="charts-container">
        <!-- Gráfico de Barras Apiladas: Ventas por Franja del Día por PDV -->
        <div class="chart-wrapper bar-chart">
          <h2>Ventas por Franja del Día por PDV</h2>
          <Bar :data="stackedBarChartData" :options="stackedBarChartOptions" />
        </div>

        <!-- Gráfico de Pastel: Distribución de Ventas por Franja -->
        <div class="chart-wrapper pie-chart">
          <h2>Distribución de Ventas por Franja</h2>
          <Pie :data="pieChartData" :options="pieChartOptions" />
        </div>
      </div>

      <!-- Tabla -->
      <div class="table-container">
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
            <tr v-for="row in filteredSalesData" :key="row.pdv">
              <td>{{ row.pdv }}</td>
              <td>{{ formatCurrency(row.morning_sales) }}</td>
              <td>{{ row.morning_part }}%</td>
              <td>{{ formatCurrency(row.afternoon_sales) }}</td>
              <td>{{ row.afternoon_part }}%</td>
              <td>{{ formatCurrency(row.night_sales) }}</td>
              <td>{{ row.night_part }}%</td>
              <td>{{ formatCurrency(row.total) }}</td>
            </tr>
            <tr class="total-row" v-if="filteredSalesData.length > 0">
              <td>{{ filteredTotals.pdv }}</td>
              <td>{{ formatCurrency(filteredTotals.morning_sales) }}</td>
              <td>{{ filteredTotals.morning_part }}%</td>
              <td>{{ formatCurrency(filteredTotals.afternoon_sales) }}</td>
              <td>{{ filteredTotals.afternoon_part }}%</td>
              <td>{{ formatCurrency(filteredTotals.night_sales) }}</td>
              <td>{{ filteredTotals.night_part }}%</td>
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
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
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
import ChartDataLabels from 'chartjs-plugin-datalabels';

// Registrar los componentes de Chart.js
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  ChartDataLabels
);

export default {
  name: 'SalesByTimeSlot',
  components: {
    Bar,
    Pie
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
    const selectedPDV = ref('Todos'); // Filtro por PDV
    const selectedDay = ref('Todos'); // Filtro por Día
    const daysInMonth = ref([]); // Lista de días del mes
    const salesData = ref([]); // Datos originales del backend
    const filteredSalesData = ref([]); // Datos filtrados por PDV
    const pdvs = ref([]);
    const filteredPdvs = ref([]); // PDVs filtrados
    const totals = ref({});
    const filteredTotals = ref({}); // Totales filtrados

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = filteredSalesData.value.length === 0 || filteredSalesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'filteredSalesData:', filteredSalesData.value);
      return result;
    });

    // Generar lista de días del mes
    const updateDaysInMonth = () => {
      if (!year.value || !month.value) return;
      const daysInMonthMap = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31};
      if (month.value === 2 && year.value % 4 === 0 && (year.value % 100 !== 0 || year.value % 400 === 0)) {
        daysInMonthMap[2] = 29;
      }
      const numDays = daysInMonthMap[month.value] || 30;
      daysInMonth.value = Array.from({ length: numDays }, (_, i) => i + 1);
      selectedDay.value = 'Todos'; // Resetear el día seleccionado al cambiar el mes
    };

    // Obtener los años disponibles con datos
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
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en available-years, redirigiendo al login');
          router.push('/login');
        } else {
          fetchData();
        }
      }
    };

    // Obtener datos de ventas por franja del día
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const params = { year: year.value, month: month.value, status: status.value };
        if (selectedPDV.value !== 'Todos') params.pdv = selectedPDV.value;
        if (selectedDay.value !== 'Todos') params.day = selectedDay.value;

        const response = await axios.get('/dashboard/sales-by-time-slot', { params });
        salesData.value = response.data.data || [];
        pdvs.value = response.data.pdvs || [];
        totals.value = response.data.totals || {};
        updateFilteredData();
        console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching sales by time slot data:', error);
        salesData.value = [];
        pdvs.value = [];
        totals.value = {};
        filteredSalesData.value = [];
        filteredPdvs.value = [];
        filteredTotals.value = {};
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Actualizar datos filtrados
    const updateFilteredData = () => {
      // Filtrar PDVs
      if (selectedPDV.value === 'Todos') {
        filteredPdvs.value = pdvs.value;
        filteredSalesData.value = salesData.value;
      } else {
        filteredPdvs.value = pdvs.value.filter(pdv => pdv === selectedPDV.value);
        filteredSalesData.value = salesData.value.filter(row => row.pdv === selectedPDV.value);
      }

      // Calcular totales filtrados
      filteredTotals.value = {
        pdv: 'TOTALES',
        morning_sales: filteredSalesData.value.reduce((sum, row) => sum + row.morning_sales, 0),
        afternoon_sales: filteredSalesData.value.reduce((sum, row) => sum + row.afternoon_sales, 0),
        night_sales: filteredSalesData.value.reduce((sum, row) => sum + row.night_sales, 0),
        total: filteredSalesData.value.reduce((sum, row) => sum + row.total, 0)
      };
      filteredTotals.value.morning_part = filteredTotals.value.total > 0 ? Math.round((filteredTotals.value.morning_sales / filteredTotals.value.total) * 100) : 0;
      filteredTotals.value.afternoon_part = filteredTotals.value.total > 0 ? Math.round((filteredTotals.value.afternoon_sales / filteredTotals.value.total) * 100) : 0;
      filteredTotals.value.night_part = filteredTotals.value.total > 0 ? Math.round((filteredTotals.value.night_sales / filteredTotals.value.total) * 100) : 0;
    };

    // Actualizar días y obtener datos al cambiar el mes
    const updateDaysAndFetch = () => {
      updateDaysInMonth();
      fetchData();
    };

    // Formatear moneda
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
    };

    // Datos para el gráfico de barras apiladas
    const stackedBarChartData = computed(() => {
      const data = {
        labels: filteredPdvs.value,
        datasets: [
          {
            label: 'Mañana',
            data: filteredSalesData.value.map(row => row.morning_sales),
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Tarde',
            data: filteredSalesData.value.map(row => row.afternoon_sales),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Noche',
            data: filteredSalesData.value.map(row => row.night_sales),
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
          title: { display: true, text: 'Punto de Venta' }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Ventas (COP)' },
          ticks: {
            callback: function(value) {
              return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
            }
          },
          stacked: true
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
          display: true,  // en false no se muestra
          anchor: 'center', // Posicionar la etiqueta en el centro de la barra
          align: 'center', // Alinear el texto al centro
          color: '#fff', // Color del texto (negro para que contraste con el fondo de la barra.  Clanco es #fff)
          font: {
            size: 11,
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

    // Datos para el gráfico de pastel (distribución por franja)
    const pieChartData = computed(() => {
      const data = {
        labels: ['Mañana', 'Tarde', 'Noche'],
        datasets: [
          {
            label: 'Distribución de Ventas',
            data: [
              filteredTotals.value.morning_sales || 0,
              filteredTotals.value.afternoon_sales || 0,
              filteredTotals.value.night_sales || 0
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
        legend: { display: true, position: 'top' },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.label || '';
              if (label) label += ': ';
              label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(context.parsed);
              return label;
            }
          }
        },
        //datalabels: {
        //  display: false, // Desactivar datalabels para los gráficos de dona
        //},
        datalabels: {
          display: true,  // en false no se muestra
          anchor: 'center', // Posicionar la etiqueta en el centro de la barra
          align: 'center', // Alinear el texto al centro
          color: '#fff', // Color del texto (negro para que contraste con el fondo de la barra.  Clanco es #fff)
          font: {
            size: 14,
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

    // Cargar años disponibles al montar el componente con verificación de autenticación
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
      status,
      selectedPDV,
      selectedDay,
      daysInMonth,
      salesData,
      filteredSalesData,
      pdvs,
      filteredPdvs,
      totals,
      filteredTotals,
      noData,
      stackedBarChartData,
      stackedBarChartOptions,
      pieChartData,
      pieChartOptions,
      fetchData,
      updateDaysAndFetch,
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
  display: flex;
  gap: 15px; /* Espaciado entre los filtros */
  align-items: center;
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
  margin-top: 120px; /* Espaciado entre los gráficos y la tabla */
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
  justify-content: center; /* Centrar los gráficos y reducir espacio */
  gap: 50px; /* Reducir el espacio entre los gráficos */
  flex-wrap: wrap; /* Permitir que los gráficos se ajusten en pantallas pequeñas */
  margin-bottom: 40px; /* Espaciado entre los gráficos y la tabla */
}

.chart-wrapper {
  height: 400px; /* Altura uniforme para ambos gráficos */
}

/* Gráfico de barras apiladas (más ancho) */
.chart-wrapper.bar-chart {
  flex: 2; /* Ocupa más espacio */
  min-width: 500px; /* Ancho mínimo */
  max-width: 1200px; /* Ancho máximo más grande */
}

/* Gráfico de pastel */
.chart-wrapper.pie-chart {
  flex: 1; /* Ocupa menos espacio */
  min-width: 300px; /* Ancho mínimo */
  max-width: 370px; /* Ancho máximo más pequeño */
}

.chart-wrapper h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>