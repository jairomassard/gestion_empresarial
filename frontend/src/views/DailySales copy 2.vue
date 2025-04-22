<template>
  <div class="daily-sales">
    <h1>Venta Diaria por PDV - {{ months[month - 1].name }} {{ year }}</h1>
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
            <th>Fecha</th>
            <th v-for="pdv in pdvs" :key="pdv">{{ pdv }}</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in dailySalesData" :key="row.date">
            <td>{{ row.date }}</td>
            <td v-for="pdv in pdvs" :key="pdv">{{ formatCurrency(row[pdv]) }}</td>
            <td>{{ formatCurrency(row.total) }}</td>
          </tr>
          <tr class="total-row" v-if="dailySalesData.length > 0">
            <td>{{ totals.date }}</td>
            <td v-for="pdv in pdvs" :key="pdv">{{ formatCurrency(totals[pdv]) }}</td>
            <td>{{ formatCurrency(totals.total) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Gráficos -->
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
            <option v-for="pdv in pdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
          </select>
        </div>
        <Line :data="lineChartData" :options="lineChartOptions" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue';
import { useStore } from 'vuex'; // Importar useStore
import { useRouter } from 'vue-router'; // Importar useRouter
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
  TimeScale
);

export default {
  name: 'DailySales',
  components: {
    Bar,
    Line
  },
  setup() {
    const store = useStore(); // Acceso al store
    const router = useRouter(); // Acceso al router

    // Datos reactivos
    const year = ref(null);
    const years = ref([]);
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1; // Mes actual (marzo = 3)
    const currentYear = currentDate.getFullYear();
    const month = ref(currentMonth); // Mes actual como predeterminado
    const months = ref([
      { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
      { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
      { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
      { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
    ]);
    const status = ref('Activo');
    const dailySalesData = ref([]);
    const pdvs = ref([]);
    const totals = ref({});
    const selectedPdv = ref('total');

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = dailySalesData.value.length > 0 && dailySalesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'dailySalesData:', dailySalesData.value);
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
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en available-years, redirigiendo al login');
          router.push('/login');
        } else {
          fetchData(); // Continúa incluso si falla, como en el original
        }
      }
    };

    // Obtener datos de ventas diarias
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const response = await axios.get('/dashboard/daily-sales', {
          params: { year: year.value, month: month.value, status: status.value }
        });
        dailySalesData.value = response.data.data || [];
        pdvs.value = response.data.pdvs || [];
        totals.value = response.data.totals || {};
        console.log('Datos recibidos:', { dailySalesData: dailySalesData.value, pdvs: pdvs.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching daily sales data:', error);
        dailySalesData.value = [];
        pdvs.value = [];
        totals.value = {};
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Formatear moneda
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
    };

    // Datos para el gráfico de barras (Ventas Totales por PDV)
    const barChartData = computed(() => {
      const data = {
        labels: pdvs.value,
        datasets: [
          {
            label: 'Ventas Totales (COP)',
            data: pdvs.value.map(pdv => totals.value[pdv] || 0),
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
        }
      }
    };

    // Datos para el gráfico de líneas (Tendencia de Ventas Diarias)
    const lineChartData = computed(() => {
      const labels = dailySalesData.value.map(row => {
        const dateStr = row.date.split(', ')[1]; // Ejemplo: "01/01/2025"
        const [day, month, year] = dateStr.split('/');
        return `${year}-${month}-${day}`; // Formato: "2025-01-01"
      });

      let data;
      if (selectedPdv.value === 'total') {
        data = dailySalesData.value.map(row => row.total);
      } else {
        data = dailySalesData.value.map(row => row[selectedPdv.value] || 0);
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
        }
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
      dailySalesData,
      pdvs,
      totals,
      noData,
      selectedPdv,
      barChartData,
      barChartOptions,
      lineChartData,
      lineChartOptions,
      fetchData,
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
  margin-top: 40px;
}
.chart-wrapper {
  margin-bottom: 40px;
  height: 400px;
  /* border: 1px solid red; */ /* Comentamos el borde de depuración */
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