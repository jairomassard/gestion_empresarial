<template>
    <div class="product-profit">
      <h1>Margen de Utilidad por Producto - {{ months[month - 1].name }} {{ year }}</h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="fetchData">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <label>Mes:</label>
        <select v-model="month" @change="fetchData">
          <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
        </select>
        <label>Producto:</label>
        <select v-model="selectedProduct" @change="fetchData">
          <option value="">Todos</option>
          <option v-for="product in products" :key="product.descripcion" :value="product.descripcion">{{ product.descripcion }}</option>
        </select>
      </div>
  
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes, año y filtros seleccionados.
      </div>
  
      <div v-if="!noData" class="charts-container">
        <div class="chart-wrapper">
          <h2>Margen de Utilidad por Producto</h2>
          <Bar :data="barChartData" :options="barChartOptions" />
        </div>
      </div>
  
      <div v-if="!noData" class="table-container">
        <table class="profit-table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Cantidad Vendida</th>
              <th>Ventas</th>
              <th>Costos</th>
              <th>Producción</th>
              <th>Utilidad</th>
              <th>Margen (%)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in productProfitData" :key="row.descripcion">
              <td>{{ row.descripcion }}</td>
              <td>{{ row.cantidad_vendida.toFixed(2) }}</td>
              <td>{{ formatCurrency(row.ventas) }}</td>
              <td>{{ formatCurrency(row.costos) }}</td>
              <td>{{ formatCurrency(row.produccion) }}</td>
              <td>{{ formatCurrency(row.utilidad) }}</td>
              <td>{{ row.margen.toFixed(2) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed } from 'vue';
  import { useStore } from 'vuex';
  import { useRouter } from 'vue-router';
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
    name: 'ProductProfit',
    components: { Bar },
    setup() {
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
      const selectedProduct = ref('');
      const products = ref([]);
      const productProfitData = ref([]);
  
      const noData = computed(() => productProfitData.value.length === 0);
  
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            fetchProducts();
            fetchData();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          if (error.response && error.response.status === 401) {
            router.push('/login');
          } else {
            fetchProducts();
            fetchData();
          }
        }
      };
  
      const fetchProducts = async () => {
        try {
          const params = { year: year.value, month: month.value };
          const response = await axios.get('/dashboard/sales-by-product', { params });
          products.value = response.data.products.map(desc => ({ descripcion: desc })) || [];
        } catch (error) {
          console.error('Error fetching products:', error);
          products.value = [];
        }
      };
  
      const fetchData = async () => {
        if (!year.value) return;
        try {
          const params = { year: year.value, month: month.value };
          if (selectedProduct.value) params.product_desc = selectedProduct.value;
          const response = await axios.get('/dashboard/product-profit', { params });
          productProfitData.value = response.data.data || [];
          console.log('Datos recibidos:', productProfitData.value);
        } catch (error) {
          console.error('Error fetching product profit data:', error);
          productProfitData.value = [];
          if (error.response && error.response.status === 401) {
            router.push('/login');
          }
        }
      };
  
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      const barChartData = computed(() => {
        const data = {
          labels: productProfitData.value.map(row => row.descripcion),
          datasets: [
            {
              label: 'Margen de Utilidad (%)',
              data: productProfitData.value.map(row => row.margen),
              backgroundColor: 'rgba(153, 102, 255, 0.6)',
              borderColor: 'rgba(153, 102, 255, 1)',
              borderWidth: 1
            }
          ]
        };
        return data;
      });
  
      const barChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Margen (%)' }
          },
          x: {
            title: { display: true, text: 'Producto' }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
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
              return `${value.toFixed(2)}%`;
            }
          }
        }
      };
  
      onMounted(() => {
        if (store.state.auth.token) {
          fetchAvailableYears();
        } else {
          router.push('/login');
        }
      });
  
      return {
        year,
        years,
        month,
        months,
        selectedProduct,
        products,
        productProfitData,
        noData,
        fetchData,
        formatCurrency,
        barChartData,
        barChartOptions
      };
    }
  };
  </script>
  
  <style scoped>
  .product-profit {
    padding: 20px;
  }
  
  .filters {
    margin-bottom: 20px;
    display: flex;
    gap: 15px;
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
    max-width: 150px;
    white-space: nowrap;
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
    margin-bottom: 40px;
    height: 400px;
  }
  
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  </style>