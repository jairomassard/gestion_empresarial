<template>
  <div class="daily-sales">
    <h1>Venta Diaria por PDV - {{ months[month - 1].name }} {{ year }}</h1>
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
      <!-- Nuevo filtro por PDV -->
      <label>PDV:</label>
      <select v-model="selectedPDV" @change="fetchData">
        <option value="Todos">Todos</option>
        <option v-for="pdv in pdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
      </select>
      <!-- Nuevo filtro por Día -->
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

    <!-- Gráficos (movidos arriba) -->
    <div v-if="!noData" class="charts-container">
      <!-- Gráfico de Barras: Ventas Totales por PDV -->
      <div class="chart-wrapper">
        <h2>Ventas Totales por PDV</h2>
        <Bar :data="barChartData" :options="barChartOptions" />
      </div>

      <!-- Gráfico de Líneas: Tendencia de Ventas Diarias -->
      <div class="chart-wrapper">
        <h2>Tendencia de Ventas Diarias</h2>
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
      <table class="sales-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th v-for="pdv in filteredPdvs" :key="pdv">{{ pdv }}</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredDailySalesData" :key="row.date">
            <td>{{ row.date }}</td>
            <td v-for="pdv in filteredPdvs" :key="pdv">{{ formatCurrency(row[pdv]) }}</td>
            <td>{{ formatCurrency(row.total) }}</td>
          </tr>
          <tr class="total-row" v-if="filteredDailySalesData.length > 0">
            <td>{{ filteredTotals.date }}</td>
            <td v-for="pdv in filteredPdvs" :key="pdv">{{ formatCurrency(filteredTotals[pdv]) }}</td>
            <td>{{ formatCurrency(filteredTotals.total) }}</td>
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
  ChartDataLabels // Añade esto al registro
);

export default {
  name: 'DailySales',
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
    const currentMonth = currentDate.getMonth() + 1; // Mes actual (marzo = 3)
    const currentYear = currentDate.getFullYear();
    const month = ref(currentMonth);
    const months = ref([
      { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
      { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
      { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
      { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
    ]);
    const status = ref('Activo');
    const selectedPDV = ref('Todos'); // Nuevo filtro por PDV
    const selectedDay = ref('Todos'); // Nuevo filtro por Día
    const daysInMonth = ref([]); // Lista de días del mes
    const dailySalesData = ref([]); // Datos originales del backend
    const filteredDailySalesData = ref([]); // Datos filtrados por PDV y Día
    const pdvs = ref([]);
    const filteredPdvs = ref([]); // PDVs filtrados
    const totals = ref({});
    const filteredTotals = ref({}); // Totales filtrados
    const selectedPdv = ref('total');

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = filteredDailySalesData.value.length === 0 || filteredDailySalesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'filteredDailySalesData:', filteredDailySalesData.value);
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

    // Obtener datos de ventas diarias
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const params = { year: year.value, month: month.value, status: status.value };
        if (selectedPDV.value !== 'Todos') params.pdv = selectedPDV.value;
        if (selectedDay.value !== 'Todos') params.day = selectedDay.value;

        const response = await axios.get('/dashboard/daily-sales', { params });
        dailySalesData.value = response.data.data || [];
        pdvs.value = response.data.pdvs || [];
        totals.value = response.data.totals || {};
        updateFilteredData();
        console.log('Datos recibidos:', { dailySalesData: dailySalesData.value, pdvs: pdvs.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching daily sales data:', error);
        dailySalesData.value = [];
        pdvs.value = [];
        totals.value = {};
        filteredDailySalesData.value = [];
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
      } else {
        filteredPdvs.value = pdvs.value.filter(pdv => pdv === selectedPDV.value);
      }

      // Filtrar datos por día (el backend ya filtra, pero lo hacemos aquí por seguridad)
      if (selectedDay.value === 'Todos') {
        filteredDailySalesData.value = dailySalesData.value;
      } else {
        const dayStr = selectedDay.value.toString().padStart(2, '0');
        const monthStr = month.value.toString().padStart(2, '0');
        const datePattern = `${dayStr}/${monthStr}/${year.value}`;
        filteredDailySalesData.value = dailySalesData.value.filter(row => row.date.includes(datePattern));
      }

      // Calcular totales filtrados
      filteredTotals.value = { date: 'TOTALES' };
      filteredPdvs.value.forEach(pdv => {
        filteredTotals.value[pdv] = filteredDailySalesData.value.reduce((sum, row) => sum + (row[pdv] || 0), 0);
      });
      filteredTotals.value.total = filteredDailySalesData.value.reduce((sum, row) => sum + row.total, 0);
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

    // Datos para el gráfico de barras (Ventas Totales por PDV)
    const barChartData = computed(() => {
      const data = {
        labels: filteredPdvs.value,
        datasets: [
          {
            label: 'Ventas Totales (COP)',
            data: filteredPdvs.value.map(pdv => filteredTotals.value[pdv] || 0),
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
            text: 'Ventas (COP)'
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

    // Datos para el gráfico de líneas (Tendencia de Ventas Diarias)
    const lineChartData = computed(() => {
      const labels = filteredDailySalesData.value.map(row => {
        const dateStr = row.date.split(', ')[1]; // Ejemplo: "01/01/2025"
        const [day, month, year] = dateStr.split('/');
        return `${year}-${month}-${day}`; // Formato: "2025-01-01"
      });

      let data;
      if (selectedPdv.value === 'total') {
        data = filteredDailySalesData.value.map(row => row.total);
      } else {
        data = filteredDailySalesData.value.map(row => row[selectedPdv.value] || 0);
      }

      const chartData = {
        labels: labels,
        datasets: [
          {
            label: selectedPdv.value === 'total' ? 'Ventas Totales (COP)' : `Ventas de ${selectedPdv.value} (COP)`,
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
            displayFormats: {
              day: 'dd/MM/yyyy'
            }
          },
          title: {
            display: true,
            text: 'Fecha'
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
          }
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
        },
        datalabels: {
          display: false, // Desactivar datalabels para los gráficos de dona
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

    // Actualizar los gráficos cuando cambie el PDV seleccionado
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
      dailySalesData,
      filteredDailySalesData,
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
.daily-sales {
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

.sales-table td:first-child {
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
  margin-bottom: 70px; /* Espaciado entre los gráficos y la tabla */
}

.chart-wrapper {
  margin-bottom: 40px;
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