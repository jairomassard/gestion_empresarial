<template>
  <div class="monthly-performance">
    <h1>Rendimiento Mensual - {{ months[month - 1].name }} {{ year }}</h1>
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

    <!-- Tabla -->
    <div class="table-container">
      <table class="performance-table">
        <thead>
          <tr>
            <th>PDV</th>
            <th>Venta Acum</th>
            <th>Venta Proy</th>
            <th>Presupuesto</th>
            <th>Cump a la Fecha</th>
            <th>% Cump Proy vs Ppto</th>
            <th>Saldo para Cumplir</th>
            <th>Venta Año Anterior</th>
            <th>Crecimiento (%)</th>
            <th>Crecimiento ($)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in dashboardData" :key="row.pdv">
            <td>{{ row.pdv }}</td>
            <td>{{ formatCurrency(row.venta_acum) }}</td>
            <td>{{ formatCurrency(row.venta_proy) }}</td>
            <td>{{ formatCurrency(row.presupuesto) }}</td>
            <td>{{ formatCurrency(row.cump_fecha) }}</td>
            <td>{{ formatPercent(row.cump_percent) }} {{ row.cump_icon }}</td>
            <td>{{ formatCurrency(row.saldo) }}</td>
            <td>{{ formatCurrency(row.venta_prev) }}</td>
            <td>{{ formatPercent(row.crecimiento_percent) }}</td>
            <td>{{ formatCurrency(row.crecimiento_valor) }}</td>
          </tr>
          <tr class="total-row" v-if="dashboardData.length > 0">
            <td>Total</td>
            <td>{{ formatCurrency(totals.venta_acum) }}</td>
            <td>{{ formatCurrency(totals.venta_proy) }}</td>
            <td>{{ formatCurrency(totals.presupuesto) }}</td>
            <td>{{ formatCurrency(totals.cump_fecha) }}</td>
            <td>{{ formatPercent(totals.cump_percent) }} {{ totals.cump_icon }}</td>
            <td>{{ formatCurrency(totals.saldo) }}</td>
            <td>{{ formatCurrency(totals.venta_prev) }}</td>
            <td>{{ formatPercent(totals.crecimiento_percent) }}</td>
            <td>{{ formatCurrency(totals.crecimiento_valor) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Gráficos -->
    <div class="charts-container" v-if="dashboardData.length > 0">
      <div class="chart">
        <h3>Venta Acumulada vs Presupuesto por PDV</h3>
        <BarChart :data="salesVsBudgetChartData" :options="chartOptions" />
      </div>
      <div class="chart">
        <h3>Distribución de Venta Acumulada por PDV</h3>
        <PieChart :data="salesDistributionChartData" :options="chartOptions" />
      </div>
    </div>
    <div v-else>
      <p>No hay datos disponibles o cargando...</p>
    </div>
  </div>
</template>

<script>
  import { ref, computed, onMounted } from 'vue';
  import { useStore } from 'vuex'; // Importar useStore para acceder al store
  import { useRouter } from 'vue-router'; // Importar useRouter para redirección
  import axios from '@/api/axios';
  import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js';
  import { Bar, Pie } from 'vue-chartjs';

  // Registrar componentes de Chart.js
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

  export default {
    name: 'MonthlyPerformance',
    components: {
      BarChart: Bar,
      PieChart: Pie
    },
    setup() {
      // Acceso al store y router
      const store = useStore();
      const router = useRouter();

      // Datos reactivos
      const year = ref(2025);
      const years = ref(Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i - 2));
      const month = ref(1); // Enero por defecto
      const months = ref([
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ]);
      const status = ref('Activo');
      const dashboardData = ref([]);
      const totals = ref({});

      // Opciones de los gráficos
      const chartOptions = ref({
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                let label = context.label || '';
                if (label) label += ': ';
                const value = context.parsed || 0;
                label += new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
                return label;
              }
            }
          },
          legend: { position: 'top' }
        }
      });

      // Datos para el gráfico de barras
      const salesVsBudgetChartData = computed(() => ({
        labels: dashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Venta Acumulada',
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            data: dashboardData.value.map(row => row.venta_acum)
          },
          {
            label: 'Presupuesto',
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            data: dashboardData.value.map(row => row.presupuesto)
          }
        ]
      }));

      // Datos para el gráfico de torta
      const salesDistributionChartData = computed(() => ({
        labels: dashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Distribución de Venta Acumulada',
            backgroundColor: [
              '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
              '#FF9F40', '#C9CBCF', '#7BCB7B', '#FF6F61'
            ],
            data: dashboardData.value.map(row => row.venta_acum)
          }
        ]
      }));

      // Métodos
      const fetchData = async () => {
        console.log('Token en el store:', store.state.auth.token); // Depuración
        try {
          const response = await axios.get('/dashboard/monthly-performance', {
            params: { year: year.value, month: month.value, status: status.value }
          });
          console.log('Datos recibidos:', response.data); // Para debug
          dashboardData.value = response.data.data || [];
          totals.value = response.data.totals || {};
        } catch (error) {
          console.error('Error fetching dashboard data:', error);
          dashboardData.value = [];
          totals.value = {};
          if (error.response && error.response.status === 401) {
            console.log('No autorizado, redirigiendo al login');
            router.push('/login');
          }
        }
      };

      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };

      const formatPercent = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'percent', minimumFractionDigits: 2 }).format(value / 100);
      };

      // Cargar datos al montar el componente
      onMounted(() => {
        if (store.state.auth.token) {
          fetchData();
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
        dashboardData,
        totals,
        chartOptions,
        salesVsBudgetChartData,
        salesDistributionChartData,
        fetchData,
        formatCurrency,
        formatPercent
      };
    }
  };
</script>

 
  <style scoped>
  .monthly-performance {
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
  .charts-container {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-top: 40px; /* Añadimos margen superior para separar de la tabla */
    margin-bottom: 30px;
    }
  .chart {
    flex: 1;
    min-width: 400px;
    height: 300px;
  }
  .table-container {
    max-width: 100%;
    overflow-x: auto;
  }
  .performance-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .performance-table th, .performance-table td {
    border: 1px solid #ddd;
    padding: 4px;
    text-align: center;
  }
  .performance-table th {
    background-color: #f2f2f2;
    font-size: 11px;
  }
  .performance-table td {
    max-width: 120px;
    white-space: nowrap;
  }
  .total-row {
    font-weight: bold;
    background-color: #f9f9f9;
  }
  </style>