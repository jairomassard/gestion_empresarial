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
      <label>PDV:</label>
      <select v-model="selectedPDV" @change="updateFilteredData">
        <option value="Todos">Todos</option>
        <option v-for="pdv in pdvList" :key="pdv" :value="pdv">{{ pdv }}</option>
      </select>
    </div>

    <!-- Gráficos Existentes (Primera Fila) -->
    <div class="charts-container" v-if="filteredDashboardData.length > 0">
      <div class="chart">
        <h3>Venta Acumulada vs Presupuesto por PDV</h3>
        <BarChart :data="salesVsBudgetChartData" :options="chartOptions" />
      </div>
      <div class="chart">
        <h3>Distribución de Venta Acumulada por PDV</h3>
        <PieChart :data="salesDistributionChartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Gráficos Adicionales (Segunda Fila) -->
    <div class="additional-charts-container" v-if="filteredDashboardData.length > 0">
      <div class="chart additional-chart">
        <h3>% Cumplimiento Proy vs Ppto y Saldo para Cumplir por PDV</h3>
        <BarChart :data="cumpVsSaldoChartData" :options="cumpVsSaldoChartOptions" />
      </div>
      <div class="chart additional-chart">
        <h3>Venta Acumulada vs Venta Año Anterior por PDV</h3>
        <BarChart :data="salesVsPrevYearChartData" :options="salesVsPrevYearChartOptions" />
      </div>
    </div>

    <div v-if="filteredDashboardData.length === 0" class="no-data">
      <p>No hay datos disponibles o cargando...</p>
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
          <tr v-for="row in filteredDashboardData" :key="row.pdv">
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
          <tr class="total-row" v-if="filteredDashboardData.length > 0">
            <td>Total</td>
            <td>{{ formatCurrency(filteredTotals.venta_acum) }}</td>
            <td>{{ formatCurrency(filteredTotals.venta_proy) }}</td>
            <td>{{ formatCurrency(filteredTotals.presupuesto) }}</td>
            <td>{{ formatCurrency(filteredTotals.cump_fecha) }}</td>
            <td>{{ formatPercent(filteredTotals.cump_percent) }} {{ filteredTotals.cump_icon }}</td>
            <td>{{ formatCurrency(filteredTotals.saldo) }}</td>
            <td>{{ formatCurrency(filteredTotals.venta_prev) }}</td>
            <td>{{ formatPercent(filteredTotals.crecimiento_percent) }}</td>
            <td>{{ formatCurrency(filteredTotals.crecimiento_valor) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>


<script>
  import { ref, computed, onMounted } from 'vue';
  import { useStore } from 'vuex';
  import { useRouter } from 'vue-router';
  import axios from '@/api/axios';
  import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement, LineElement, PointElement } from 'chart.js';
  import { Bar, Pie } from 'vue-chartjs';
  import ChartDataLabels from 'chartjs-plugin-datalabels';

  // Registrar componentes de Chart.js
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement, LineElement, PointElement, ChartDataLabels);

  export default {
    name: 'MonthlyPerformance',
    components: {
      BarChart: Bar,
      PieChart: Pie
    },
    setup() {
      const store = useStore();
      const router = useRouter();

      // Datos reactivos
      const year = ref(2025);
      const years = ref(Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i - 2));
      const month = ref(1);
      const months = ref([
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ]);
      const status = ref('Activo');
      const selectedPDV = ref('Todos');
      const pdvList = ref([]);
      const dashboardData = ref([]);
      const filteredDashboardData = ref([]);
      const totals = ref({});

      // Opciones de los gráficos existentes
      const chartOptions = ref({
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                const value = context.raw || 0; // Usar context.raw en lugar de context.parsed
                return label + new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          datalabels: {
            display: false, // Desactivar datalabels para los gráficos de dona
          },
          legend: { position: 'top' }
        }
      });

      // Opciones para el gráfico combinado (% Cump Proy vs Ppto y Saldo para Cumplir)
      const cumpVsSaldoChartOptions = ref({
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Saldo para Cumplir (COP)'
            },
            ticks: {
              callback: (value) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value)
            }
          },
          y1: {
            position: 'right',
            beginAtZero: true,
            max: 200,
            title: {
              display: true,
              text: '% Cumplimiento Proy vs Ppto'
            },
            ticks: {
              callback: (value) => `${value}%`
            },
            grid: {
              drawOnChartArea: false
            }
          },
          x: {
            title: {
              display: true,
              text: 'PDV'
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                const value = context.raw || 0; // Usar context.raw
                if (context.dataset.yAxisID === 'y1') {
                  return label + `${value}%`;
                }
                return label + new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          datalabels: {
            display: false, // Desactivar datalabels para los gráficos de dona
          },
          legend: { position: 'top' }
        }
      });

      // Opciones para el nuevo gráfico (Venta Acumulada vs Venta Año Anterior)
      const salesVsPrevYearChartOptions = ref({
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Valor (COP)'
            },
            ticks: {
              callback: (value) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value)
            }
          },
          x: {
            title: {
              display: true,
              text: 'PDV'
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                const value = context.raw || 0;
                return label + new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
              }
            }
          },
          datalabels: {
            display: false, // Desactivar datalabels para los gráficos de dona
          },
          legend: { position: 'top' }
        }
      });

      // Datos para el gráfico de barras (Venta Acumulada vs Presupuesto)
      const salesVsBudgetChartData = computed(() => ({
        labels: filteredDashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Venta Acumulada',
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            data: filteredDashboardData.value.map(row => Number(row.venta_acum) || 0) // Asegurar que sea numérico
          },
          {
            label: 'Presupuesto',
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            data: filteredDashboardData.value.map(row => Number(row.presupuesto) || 0) // Asegurar que sea numérico
          }
        ]
      }));

      // Datos para el gráfico de torta (Distribución de Venta Acumulada)
      const salesDistributionChartData = computed(() => ({
        labels: filteredDashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Distribución de Venta Acumulada',
            backgroundColor: [
              '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
              '#FF9F40', '#C9CBCF', '#7BCB7B', '#FF6F61'
            ],
            data: filteredDashboardData.value.map(row => Number(row.venta_acum) || 0) // Asegurar que sea numérico
          }
        ]
      }));

      // Datos para el gráfico combinado (% Cump Proy vs Ppto y Saldo para Cumplir)
      const cumpVsSaldoChartData = computed(() => ({
        labels: filteredDashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Saldo para Cumplir',
            type: 'bar',
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            data: filteredDashboardData.value.map(row => Number(row.saldo) || 0), // Asegurar que sea numérico
            yAxisID: 'y'
          },
          {
            label: '% Cump Proy vs Ppto',
            type: 'line',
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            data: filteredDashboardData.value.map(row => Number(row.cump_percent) || 0), // Asegurar que sea numérico
            yAxisID: 'y1',
            fill: false,
            tension: 0.1
          }
        ]
      }));

      // Datos para el nuevo gráfico (Venta Acumulada vs Venta Año Anterior)
      const salesVsPrevYearChartData = computed(() => ({
        labels: filteredDashboardData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Venta Acumulada',
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            data: filteredDashboardData.value.map(row => Number(row.venta_acum) || 0) // Asegurar que sea numérico
          },
          {
            label: 'Venta Año Anterior',
            backgroundColor: 'rgba(153, 102, 255, 0.6)',
            data: filteredDashboardData.value.map(row => Number(row.venta_prev) || 0) // Asegurar que sea numérico
          }
        ]
      }));

      // Totales filtrados
      const filteredTotals = computed(() => {
        if (filteredDashboardData.value.length === 0) return {};
        return filteredDashboardData.value.reduce((acc, row) => ({
          venta_acum: (acc.venta_acum || 0) + (Number(row.venta_acum) || 0),
          venta_proy: (acc.venta_proy || 0) + (Number(row.venta_proy) || 0),
          presupuesto: (acc.presupuesto || 0) + (Number(row.presupuesto) || 0),
          cump_fecha: (acc.cump_fecha || 0) + (Number(row.cump_fecha) || 0),
          cump_percent: row.cump_percent, // Esto podría necesitar un cálculo más complejo
          cump_icon: row.cump_icon, // Esto podría necesitar un cálculo más complejo
          saldo: (acc.saldo || 0) + (Number(row.saldo) || 0),
          venta_prev: (acc.venta_prev || 0) + (Number(row.venta_prev) || 0),
          crecimiento_percent: row.crecimiento_percent, // Esto podría necesitar un cálculo más complejo
          crecimiento_valor: (acc.crecimiento_valor || 0) + (Number(row.crecimiento_valor) || 0)
        }), {});
      });

      // Obtener datos del backend
      const fetchData = async () => {
        console.log('Token en el store:', store.state.auth.token);
        try {
          const response = await axios.get('/dashboard/monthly-performance', {
            params: { year: year.value, month: month.value, status: status.value }
          });
          console.log('Datos recibidos:', response.data);
          dashboardData.value = response.data.data || [];
          totals.value = response.data.totals || {};

          // Actualizar la lista de PDVs
          pdvList.value = [...new Set(dashboardData.value.map(row => row.pdv))].sort();

          // Actualizar datos filtrados
          updateFilteredData();
        } catch (error) {
          console.error('Error fetching dashboard data:', error);
          dashboardData.value = [];
          totals.value = {};
          pdvList.value = [];
          filteredDashboardData.value = [];
          if (error.response && error.response.status === 401) {
            console.log('No autorizado, redirigiendo al login');
            router.push('/login');
          }
        }
      };

      // Actualizar datos filtrados según el PDV seleccionado
      const updateFilteredData = () => {
        if (selectedPDV.value === 'Todos') {
          filteredDashboardData.value = dashboardData.value;
        } else {
          filteredDashboardData.value = dashboardData.value.filter(row => row.pdv === selectedPDV.value);
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
        selectedPDV,
        pdvList,
        dashboardData,
        filteredDashboardData,
        totals,
        filteredTotals,
        chartOptions,
        cumpVsSaldoChartOptions,
        salesVsPrevYearChartOptions,
        salesVsBudgetChartData,
        salesDistributionChartData,
        cumpVsSaldoChartData,
        salesVsPrevYearChartData,
        fetchData,
        updateFilteredData,
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
    display: flex;
    gap: 15px;
    align-items: center;
  }

  label {
    margin-right: 5px;
    font-weight: bold;
  }

  select {
    padding: 5px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }

  /* Contenedor de las dos primeras gráficas (Venta Acumulada vs Presupuesto y Distribución de Venta Acumulada) */
  .charts-container {
    display: flex;
    flex-wrap: wrap;
    gap: 20px; /* Espaciado entre las dos primeras gráficas. Ajusta este valor para cambiar la separación entre ellas. */
    margin-bottom: 120px; /* Espaciado entre las primeras gráficas y las adicionales. Ajusta este valor para cambiar la separación vertical. */
  }

  /* Estilo de cada gráfica en el contenedor de las primeras gráficas */
  .chart {
    flex: 1; /* Permite que las gráficas se expandan para llenar el espacio disponible */
    min-width: 400px; /* Ancho mínimo de cada gráfica. Ajusta este valor si quieres que las gráficas sean más anchas o más estrechas en pantallas pequeñas. */
    height: 300px; /* Altura de las gráficas. Ajusta este valor para hacer las gráficas más altas o más bajas. */
  }

  /* Contenedor de las dos últimas gráficas (% Cumplimiento Proy vs Ppto y Saldo para Cumplir, y Venta Acumulada vs Venta Año Anterior) */
  .additional-charts-container {
    display: flex;
    flex-wrap: wrap;
    gap: 20px; /* Espaciado entre las dos últimas gráficas. Ajusta este valor para cambiar la separación entre ellas. Debe ser igual al gap de .charts-container para consistencia. */
    margin-bottom: 120px; /* Espaciado entre las gráficas adicionales y la tabla. Ajusta este valor para cambiar la separación vertical. */
  }

  /* Estilo de cada gráfica en el contenedor de las gráficas adicionales */
  .additional-chart {
    flex: 1; /* Permite que las gráficas se expandan para llenar el espacio disponible, igual que las primeras gráficas */
    min-width: 400px; /* Ancho mínimo de cada gráfica. Ajusta este valor si quieres que las gráficas sean más anchas o más estrechas en pantallas pequeñas. Debe ser igual al min-width de .chart para consistencia. */
    /* max-width: 600px; <- Comentado: Eliminar el max-width para que las gráficas se expandan como las primeras. Si deseas limitar el ancho máximo, descomenta y ajusta este valor. */
    height: 300px; /* Altura de las gráficas. Ajusta este valor para hacer las gráficas más altas o más bajas. Debe ser igual a la altura de .chart para consistencia. */
  }

  .table-container {
    max-width: 100%;
    overflow-x: auto;
    margin-top: 130px; /* Espaciado entre la tabla y las gráficas adicionales. Ajusta este valor para cambiar la separación vertical. */
  }

  .performance-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .performance-table th,
  .performance-table td {
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

  .no-data {
    text-align: center;
    padding: 20px;
    color: #888;
  }
</style>