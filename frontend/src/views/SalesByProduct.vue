<template>
  <div class="sales-by-product">
    <h1>
      Ventas por Producto - {{ month === 0 ? 'Todos los meses' : months.find(m => m.num === month)?.name }}
      <span v-if="day && month !== 0"> {{ day }} </span>
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
      <select v-model="day" @change="fetchData" :disabled="month === 0">
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
      <label>Producto:</label>
      <select v-model="selectedProduct" @change="applyProductFilter">
        <option value="">Todos los productos</option>
        <option v-for="product in products" :key="product" :value="product">{{ product }}</option>
      </select>
    </div>

    <!-- Botones para ordenar -->
    <div class="sort-buttons">
      <button @click="sortByName">Ordenar por Nombre</button>
      <button @click="sortByTotal">Ordenar por Total (Mayor a Menor)</button>
    </div>

    <!-- Mensaje si no hay datos -->
    <div v-if="noData" class="no-data-message">
      No hay datos disponibles para el período, estatus y PDV seleccionados.
    </div>

    <!-- Contenedor para gráficos y tabla -->
    <div v-else>
      <!-- Gráficos (Top 10 Más Vendidos y Top 20 Menos Vendidos) -->
      <div class="charts-container">
        <!-- Gráfico de Barras Horizontales: Top 10 Productos Más Vendidos -->
        <div class="chart-wrapper top-bar-chart">
          <h2>Top 10 Productos Más Vendidos</h2>
          <Bar :data="horizontalBarChartData" :options="horizontalBarChartOptions" />
        </div>

        <!-- Gráfico de Barras Horizontales: Top 20 Productos Menos Vendidos -->
        <div class="chart-wrapper bottom-bar-chart">
          <h2>Top 20 Productos Menos Vendidos</h2>
          <Bar :data="bottomBarChartData" :options="bottomBarChartOptions" />
        </div>
      </div>

      <!-- Tabla -->
      <div class="table-container">
        <table class="sales-table">
          <thead>
            <tr>
              <th>Producto</th>
              <th v-for="pdv in pdvs" :key="pdv">{{ pdv }}</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredSalesData" :key="row.product">
              <td>{{ row.product }}</td>
              <td v-for="pdv in pdvs" :key="pdv">{{ formatCurrency(row[pdv]) }}</td>
              <td>{{ formatCurrency(row.total) }}</td>
            </tr>
            <tr class="total-row" v-if="filteredSalesData.length > 0">
              <td>{{ totals.product }}</td>
              <td v-for="pdv in pdvs" :key="pdv">{{ formatCurrency(totals[pdv]) }}</td>
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
import ChartDataLabels from 'chartjs-plugin-datalabels';

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
  name: 'SalesByProduct',
  components: {
    Bar
  },
  setup() {
    // Datos reactivos
    const year = ref(null);
    const years = ref([]);
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1;
    const currentYear = currentDate.getFullYear();
    const month = ref(currentMonth);

    const months = ref([
      { num: 0, name: 'Todos los meses' }, // Añadir opción para todos los meses
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
    const filteredSalesData = ref([]);
    const pdvs = ref([]);
    const products = ref([]);
    const totals = ref({});
    const selectedProduct = ref('');

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      const result = filteredSalesData.value.length === 0 || filteredSalesData.value.every(row => row.total === 0);
      console.log('noData:', result, 'filteredSalesData:', filteredSalesData.value);
      return result;
    });

    // Computed para filtrar los PDVs según el estatus seleccionado
    const filteredPdvs = computed(() => {
      return allPdvs.value;
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
        fetchData();
      }
    };

    // Actualizar la lista de días disponibles según el año y mes seleccionados
    const updateDays = () => {
      if (!year.value || month.value === 0) {
        days.value = [];
        day.value = null;
        return;
      }
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

    // Combinar fetchData para cuando cambie el estatus
    const updatePdvsAndFetchData = () => {
      if (selectedPdv.value && !filteredPdvs.value.includes(selectedPdv.value)) {
        selectedPdv.value = null;
      }
      fetchData();
    };

    // Obtener datos de ventas por producto
    const fetchData = async () => {
      if (!year.value) return;
      try {
        const response = await axios.get('/dashboard/sales-by-product', {
          params: {
            year: year.value,
            month: month.value === 0 ? null : month.value, // Enviar null para "Todos los meses"
            day: month.value === 0 ? null : day.value, // No enviar día si es "Todos los meses"
            status: status.value,
            pdv: selectedPdv.value
          }
        });
        salesData.value = response.data.data || [];
        filteredSalesData.value = [...salesData.value];
        pdvs.value = response.data.pdvs || [];
        allPdvs.value = response.data.pdvs || [];
        products.value = response.data.products || [];
        totals.value = response.data.totals || {};
        console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, products: products.value, totals: totals.value });
      } catch (error) {
        console.error('Error fetching sales by product data:', error);
        salesData.value = [];
        filteredSalesData.value = [];
        pdvs.value = [];
        allPdvs.value = [];
        products.value = [];
        totals.value = {};
      }
    };

    // Filtro por producto
    const applyProductFilter = () => {
      if (selectedProduct.value) {
        filteredSalesData.value = salesData.value.filter(row => row.product === selectedProduct.value);
      } else {
        filteredSalesData.value = [...salesData.value];
      }
      sortByTotal();
    };

    // Ordenar por nombre
    const sortByName = () => {
      filteredSalesData.value.sort((a, b) => a.product.localeCompare(b.product));
    };

    // Ordenar por total (de mayor a menor)
    const sortByTotal = () => {
      filteredSalesData.value.sort((a, b) => b.total - a.total);
    };

    // Formatear moneda
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
    };

    // Datos para el gráfico de barras horizontales (Top 10 productos más vendidos)
    const horizontalBarChartData = computed(() => {
      const topProducts = [...salesData.value]
        .sort((a, b) => b.total - a.total)
        .slice(0, 10);

      const labels = topProducts.map(row => row.product);
      const data = topProducts.map(row => row.total);

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
            text: 'Producto'
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
          anchor: 'center',
          align: 'center',
          color: '#fff',
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

    // Datos para el gráfico de barras horizontales (Top 20 productos menos vendidos)
    const bottomBarChartData = computed(() => {
      const bottomProducts = [...salesData.value]
        .sort((a, b) => a.total - b.total)
        .slice(0, 20);

      const labels = bottomProducts.map(row => row.product);
      const data = bottomProducts.map(row => row.total);

      const chartData = {
        labels: labels,
        datasets: [
          {
            label: 'Ventas (COP)',
            data: data,
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
          }
        ]
      };
      console.log('bottomBarChartData:', chartData);
      return chartData;
    });

    const bottomBarChartOptions = {
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
            text: 'Producto'
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
          anchor: 'center',
          align: 'center',
          color: '#fff',
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

    // Cargar años disponibles al montar el componente
    onMounted(() => {
      fetchAvailableYears();
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
      filteredSalesData,
      pdvs,
      allPdvs,
      products,
      totals,
      selectedProduct,
      noData,
      horizontalBarChartData,
      horizontalBarChartOptions,
      bottomBarChartData,
      bottomBarChartOptions,
      fetchData,
      updateDaysAndFetchData,
      updatePdvsAndFetchData,
      applyProductFilter,
      sortByName,
      sortByTotal,
      formatCurrency
    };
  }
};
</script>

<style scoped>
.sales-by-product {
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
  gap: 50px;
  justify-content: center;
  max-width: 1600px; /* Aumentado para dar más espacio a los gráficos */
  margin: 0 auto;
  margin-bottom: 20px;
}

.chart-wrapper {
  /* Ajusta la altura de los gráficos aquí */
  height: 400px; /* Cambia este valor para aumentar o disminuir la altura */
}

/* Gráfico de barras horizontales (Top 10 Más Vendidos) */
.chart-wrapper.top-bar-chart {
  flex: 1;
  /* Ajusta el ancho del gráfico de "Top 10 Más Vendidos" aquí */
  min-width: 500px; /* Ancho mínimo */
  max-width: 1000px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
}

/* Gráfico de barras horizontales (Top 20 Menos Vendidos) */
.chart-wrapper.bottom-bar-chart {
  flex: 1;
  /* Ajusta el ancho del gráfico de "Top 20 Menos Vendidos" aquí */
  min-width: 600px; /* Ancho mínimo */
  max-width: 1000px; /* Ancho máximo - aumenta o disminuye este valor para cambiar el ancho */
  /* Ajusta la altura del gráfico de "Top 20 Menos Vendidos" aquí (si quieres una altura diferente) */
  height: 600px; /* Cambia este valor para aumentar o disminuir la altura */
}

.chart-wrapper h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>