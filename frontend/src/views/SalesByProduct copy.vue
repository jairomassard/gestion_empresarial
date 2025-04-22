<template>
    <div class="sales-by-product">
      <h1>Ventas por Producto - {{ months[month - 1].name }} {{ year }}</h1>
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
        No hay datos disponibles para el mes y año seleccionados.
      </div>
  
      <!-- Tabla -->
      <div v-else class="table-container">
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
  
      <!-- Gráficos -->
      <div v-if="!noData" class="charts-container">
        <!-- Gráfico de Barras Horizontales: Top 10 Productos Más Vendidos -->
        <div class="chart-wrapper">
          <h2>Top 10 Productos Más Vendidos</h2>
          <Bar :data="horizontalBarChartData" :options="horizontalBarChartOptions" />
        </div>
  
        <!-- Gráfico de Dona: Distribución de Ventas por Producto (Top 10) -->
        <div class="chart-wrapper">
          <h2>Distribución de Ventas (Top 10 Productos)</h2>
          <Doughnut :data="doughnutChartData" :options="doughnutChartOptions" />
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed } from 'vue';
  import axios from '@/api/axios';
  import { Bar, Doughnut } from 'vue-chartjs';
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
    name: 'SalesByProduct',
    components: {
      Bar,
      Doughnut
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
      const filteredSalesData = ref([]);
      const pdvs = ref([]);
      const products = ref([]);
      const totals = ref({});
      const selectedProduct = ref(''); // Filtro por producto
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        const result = filteredSalesData.value.length > 0 && filteredSalesData.value.every(row => row.total === 0);
        console.log('noData:', result, 'filteredSalesData:', filteredSalesData.value);
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
  
      // Obtener datos de ventas por producto
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const response = await axios.get('/dashboard/sales-by-product', {
            params: { year: year.value, month: month.value, status: status.value }
          });
          salesData.value = response.data.data || [];
          filteredSalesData.value = [...salesData.value]; // Inicialmente mostramos todos los datos
          pdvs.value = response.data.pdvs || [];
          products.value = response.data.products || [];
          totals.value = response.data.totals || {};
          console.log('Datos recibidos:', { salesData: salesData.value, pdvs: pdvs.value, products: products.value, totals: totals.value });
        } catch (error) {
          console.error('Error fetching sales by product data:', error);
          salesData.value = [];
          filteredSalesData.value = [];
          pdvs.value = [];
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
        sortByTotal(); // Ordenar por total después de filtrar
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
        // Ordenar los datos por total y tomar los primeros 10
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
        indexAxis: 'y', // Hacer las barras horizontales
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
            display: false // No necesitamos leyenda para un solo dataset
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
          }
        }
      };
  
      // Datos para el gráfico de dona (distribución por producto, Top 10)
      const doughnutChartData = computed(() => {
        // Ordenar los datos por total y tomar los primeros 10
        const topProducts = [...salesData.value]
          .sort((a, b) => b.total - a.total)
          .slice(0, 10);
  
        const colors = [
          'rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)', 'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)', 'rgba(153, 102, 255, 0.6)', 'rgba(255, 159, 64, 0.6)',
          'rgba(255, 99, 132, 0.4)', 'rgba(54, 162, 235, 0.4)', 'rgba(75, 192, 192, 0.4)',
          'rgba(255, 206, 86, 0.4)'
        ];
        const borderColors = colors.map(color => color.replace('0.6', '1').replace('0.4', '1'));
  
        const data = {
          labels: topProducts.map(row => row.product),
          datasets: [
            {
              label: 'Distribución de Ventas',
              data: topProducts.map(row => row.total),
              backgroundColor: colors,
              borderColor: borderColors,
              borderWidth: 1
            }
          ]
        };
        console.log('doughnutChartData:', data);
        return data;
      });
  
      const doughnutChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right'
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
        filteredSalesData,
        pdvs,
        products,
        totals,
        selectedProduct,
        noData,
        horizontalBarChartData,
        horizontalBarChartOptions,
        doughnutChartData,
        doughnutChartOptions,
        fetchData,
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
    margin-bottom: 20px;
  }
  label {
    margin-right: 10px;
  }
  select {
    padding: 5px;
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
  .sales-table td:first-child { /* Columna "Producto" */
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
    margin-top: 40px;
  }
  .chart-wrapper {
    margin-bottom: 60px;
    height: 500px; /* Aumentamos la altura */
    max-width: 1000px; /* Aumentamos el ancho */
    margin-left: auto;
    margin-right: auto;
  }
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  </style>