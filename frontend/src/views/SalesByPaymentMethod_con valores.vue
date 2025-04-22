<template>
  <div class="sales-by-payment-method">
    <!-- Actualizar el título para incluir el día si está seleccionado -->
    <h1>
      Ventas por Medio de Pago - {{ months[month - 1].name }}
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
      <select v-model="status" @change="updatePdvsAndFetchData">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <label>PDV:</label>
      <select v-model="selectedPdv" @change="fetchData">
        <option :value="null">Todos los PDVs</option>
        <option v-for="pdv in filteredPdvs" :key="pdv" :value="pdv">{{ pdv }}</option>
      </select>
    </div>

    <!-- Mensaje si no hay datos -->
    <div v-if="noData" class="no-data-message">
      No hay datos disponibles para el mes, año, día y PDV seleccionados.
    </div>

    <!-- Contenedor para gráficos y tabla -->
    <div v-if="!noData">
      <!-- Gráficos (movidos arriba) -->
      <div class="charts-container">
        <!-- Gráfico de Barras Apiladas: Ventas por Medio de Pago por PDV -->
        <div class="chart-wrapper bar-chart">
          <h2>Ventas por Medio de Pago por PDV</h2>
          <Bar :data="stackedBarChartData" :options="stackedBarChartOptions" />
        </div>

        <!-- Gráfico de Pastel: Distribución de Ventas por Medio de Pago -->
        <div class="chart-wrapper pie-chart">
          <h2>Distribución de Ventas por Medio de Pago</h2>
          <Pie :data="pieChartData" :options="pieChartOptions" />
        </div>
      </div>

      <!-- Tabla (movida abajo) -->
      <div class="table-container">
        <table class="sales-table">
          <thead>
            <tr>
              <th>PDV</th>
              <th>Bonos</th>
              <th>Efectivo</th>
              <th>Recibo Bancario</th>
              <th>Tarjeta Débito</th>
              <th>Transferencia Bancaria</th>
              <th>Vale</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in salesData" :key="row.pdv">
              <td>{{ row.pdv }}</td>
              <td>{{ formatCurrency(row.bonos) }}</td>
              <td>{{ formatCurrency(row.efectivo) }}</td>
              <td>{{ formatCurrency(row.recibo_bancario) }}</td>
              <td>{{ formatCurrency(row.tarjeta_debito) }}</td>
              <td>{{ formatCurrency(row.transferencia_bancaria) }}</td>
              <td>{{ formatCurrency(row.vale) }}</td>
              <td>{{ formatCurrency(row.total) }}</td>
            </tr>
            <tr class="total-row" v-if="salesData.length > 0">
              <td>{{ totals.pdv }}</td>
              <td>{{ formatCurrency(totals.bonos) }}</td>
              <td>{{ formatCurrency(totals.efectivo) }}</td>
              <td>{{ formatCurrency(totals.recibo_bancario) }}</td>
              <td>{{ formatCurrency(totals.tarjeta_debito) }}</td>
              <td>{{ formatCurrency(totals.transferencia_bancaria) }}</td>
              <td>{{ formatCurrency(totals.vale) }}</td>
              <td>{{ formatCurrency(totals.total) }}</td>
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
import ChartDataLabels from 'chartjs-plugin-datalabels'; // Importar el plugin

// Registrar los componentes de Chart.js y el plugin
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  ChartDataLabels // Registrar el plugin
);

export default {
  name: 'SalesByPaymentMethod',
  components: {
    Bar,
    Pie
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
    const selectedPdv = ref(null);
    const allPdvs = ref([]);
    const salesData = ref([]);
    const totals = ref({});

    // Variable para activar/desactivar las etiquetas en los gráficos
    const showDataLabels = ref(false); // Cambia a false para desactivar las etiquetas

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = salesData.value.length > 0 && salesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'salesData:', salesData.value);
      return result;
    });

    // Computed para filtrar los PDVs según el estatus seleccionado
    const filteredPdvs = computed(() => {
      if (status.value === 'Todos') {
        return allPdvs.value.map(pdv => pdv.pdv);
      }
      return allPdvs.value
        .filter(pdv => pdv.estado === status.value)
        .map(pdv => pdv.pdv);
    });

    // Obtener los años disponibles con datos
    const fetchAvailableYears = async () => {
      try {
        const response = await axios.get('/available-years');
        years.value = response.data.years || [];
        if (years.value.length > 0) {
          year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
          updateDays();
          fetchPdvs();
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
          updateDays();
          fetchPdvs();
          fetchData();
        }
      }
    };

    // Obtener todos los PDVs con su estado
    const fetchPdvs = async () => {
      try {
        const response = await axios.get('/pdvs');
        allPdvs.value = response.data.pdvs || [];
        console.log('PDVs obtenidos:', allPdvs.value);
      } catch (error) {
        console.error('Error fetching PDVs:', error);
        allPdvs.value = [];
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en pdvs, redirigiendo al login');
          router.push('/login');
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

    // Combinar fetchPdvs y fetchData para cuando cambie el estatus
    const updatePdvsAndFetchData = () => {
      if (selectedPdv.value && !filteredPdvs.value.includes(selectedPdv.value)) {
        selectedPdv.value = null;
      }
      fetchData();
    };

    // Obtener datos de ventas por medio de pago
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const response = await axios.get('/dashboard/sales-by-payment-method', {
          params: {
            year: year.value,
            month: month.value,
            day: day.value,
            status: status.value,
            pdv: selectedPdv.value
          }
        });
        salesData.value = response.data.data || [];
        totals.value = response.data.totals || {};
        console.log('Datos recibidos:', { salesData: salesData.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching sales by payment method data:', error);
        salesData.value = [];
        totals.value = {};
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Formatear moneda para la tabla
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
    };

    // Formatear valores en millones (ej. 33.287.700 → 33,28M)
    const formatInMillions = (value) => {
      if (value >= 1_000_000) {
        const millions = value / 1_000_000;
        return `${millions.toFixed(2).replace(/\.00$/, '')}M`;
      }
      return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 0 }).format(value);
    };

    // Datos para el gráfico de barras apiladas
    const stackedBarChartData = computed(() => {
      const data = {
        labels: salesData.value.map(row => row.pdv),
        datasets: [
          {
            label: 'Bonos',
            data: salesData.value.map(row => row.bonos),
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Efectivo',
            data: salesData.value.map(row => row.efectivo),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Recibo Bancario',
            data: salesData.value.map(row => row.recibo_bancario),
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Tarjeta Débito',
            data: salesData.value.map(row => row.tarjeta_debito),
            backgroundColor: 'rgba(255, 206, 86, 0.6)',
            borderColor: 'rgba(255, 206, 86, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Transferencia Bancaria',
            data: salesData.value.map(row => row.transferencia_bancaria),
            backgroundColor: 'rgba(153, 102, 255, 0.6)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          },
          {
            label: 'Vale',
            data: salesData.value.map(row => row.vale),
            backgroundColor: 'rgba(255, 159, 64, 0.6)',
            borderColor: 'rgba(255, 159, 64, 1)',
            borderWidth: 1,
            stack: 'Stack 0'
          }
        ]
      };
      console.log('stackedBarChartData:', data);
      return data;
    });

    const stackedBarChartOptions = computed(() => ({
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
              return formatInMillions(value); // Formato en millones para el eje Y
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
              label += formatInMillions(context.parsed.y); // Formato en millones para el tooltip
              return label;
            }
          }
        },
        datalabels: {
          display: showDataLabels.value, // Activar/desactivar etiquetas
          color: '#000',
          anchor: 'end',
          align: 'top',
          formatter: (value) => formatInMillions(value), // Formato en millones para las etiquetas
          font: {
            weight: 'bold',
            size: 12
          }
        }
      }
    }));

    // Datos para el gráfico de pastel
    const pieChartData = computed(() => {
      const data = {
        labels: ['Bonos', 'Efectivo', 'Recibo Bancario', 'Tarjeta Débito', 'Transferencia Bancaria', 'Vale'],
        datasets: [
          {
            label: 'Distribución de Ventas',
            data: [
              totals.value.bonos || 0,
              totals.value.efectivo || 0,
              totals.value.recibo_bancario || 0,
              totals.value.tarjeta_debito || 0,
              totals.value.transferencia_bancaria || 0,
              totals.value.vale || 0
            ],
            backgroundColor: [
              'rgba(255, 99, 132, 0.6)',
              'rgba(54, 162, 235, 0.6)',
              'rgba(75, 192, 192, 0.6)',
              'rgba(255, 206, 86, 0.6)',
              'rgba(153, 102, 255, 0.6)',
              'rgba(255, 159, 64, 0.6)'
            ],
            borderColor: [
              'rgba(255, 99, 132, 1)',
              'rgba(54, 162, 235, 1)',
              'rgba(75, 192, 192, 1)',
              'rgba(255, 206, 86, 1)',
              'rgba(153, 102, 255, 1)',
              'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
          }
        ]
      };
      console.log('pieChartData:', data);
      return data;
    });

    const pieChartOptions = computed(() => ({
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
              label += formatInMillions(context.parsed); // Formato en millones para el tooltip
              return label;
            }
          }
        },
        datalabels: {
          display: showDataLabels.value, // Activar/desactivar etiquetas
          color: '#000',
          formatter: (value) => formatInMillions(value), // Formato en millones para las etiquetas
          font: {
            weight: 'bold',
            size: 12
          }
        }
      }
    }));

    // Cargar años y PDVs disponibles al montar el componente
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
      selectedPdv,
      filteredPdvs,
      salesData,
      totals,
      noData,
      stackedBarChartData,
      stackedBarChartOptions,
      pieChartData,
      pieChartOptions,
      fetchData,
      updateDaysAndFetchData,
      updatePdvsAndFetchData,
      formatCurrency
    };
  }
};
</script>

<style scoped>
.sales-by-payment-method {
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

.table-container {
  overflow-x: auto;
  /* Ajusta la separación entre los gráficos y la tabla aquí */
  margin-top: 120px; /* Cambia este valor para aumentar o disminuir la separación */
  margin-bottom: 40px;
}

.sales-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.sales-table th,
.sales-table td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: right;
}

.sales-table th {
  background-color: #f4f4f4;
  font-weight: bold;
}

.sales-table td:first-child,
.sales-table th:first-child {
  text-align: left;
}

.total-row {
  font-weight: bold;
  background-color: #e0e0e0;
}

.no-data-message {
  text-align: center;
  color: #888;
  margin: 20px 0;
}

.charts-container {
  display: flex;
  flex-wrap: wrap;
  /* Ajusta la separación entre los gráficos aquí */
  gap: 50px; /* Cambia este valor para aumentar o disminuir la separación entre gráficos */
  justify-content: center;
  max-width: 1200px;
  margin: 0 auto;
}

.chart-wrapper {
  /* Ajusta la altura de los gráficos aquí */
  height: 400px; /* Cambia este valor para aumentar o disminuir la altura */
}

/* Gráfico de barras apiladas */
.chart-wrapper.bar-chart {
  flex: 2;
  /* Ajusta el ancho del gráfico de barras aquí */
  min-width: 500px; /* Ancho mínimo */
  max-width: 1200px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
}

/* Gráfico de pastel */
.chart-wrapper.pie-chart {
  flex: 1;
  /* Ajusta el ancho del gráfico de pastel aquí */
  min-width: 300px; /* Ancho mínimo */
  max-width: 500px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
}

.chart-wrapper h2 {
  text-align: center;
  margin-bottom: 10px;
}
</style>