<template>
    <div class="product-profit">
      <h1>Margen de Utilidad por Producto - {{ months[month - 1].name }} {{ year }} <span v-if="day"> (Día {{ day }})</span></h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="updateDaysAndFetch">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <label>Mes:</label>
        <select v-model="month" @change="updateDaysAndFetch">
          <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
        </select>
        <label>Día:</label>
        <select v-model="day" @change="fetchData">
          <option value="">Todos</option>
          <option v-for="d in daysInMonth" :key="d" :value="d">{{ d }}</option>
        </select>
        <label>Producto:</label>
        <select v-model="selectedProduct" @change="fetchData">
          <option value="">Todos</option>
          <option v-for="product in products" :key="product.descripcion" :value="product.descripcion">{{ product.descripcion }}</option>
        </select>
      </div>
  
      <div class="actions">
        <button @click="exportToExcel">Exportar a Excel</button>
        <button @click="downloadChart('profitChart')">Descargar Gráfico de Margen</button>
        <button @click="downloadChart('salesVsCostsChart')">Descargar Gráfico de Ventas y Costos</button>
      </div>
  
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes, año, día y filtros seleccionados.
      </div>
  
      <div v-if="!noData" class="charts-container">
        <div class="chart-wrapper">
          <h2>Margen y Utilidad por Producto ({{ chartData.length < productProfitData.length ? 'Top 10' : 'Todos' }})</h2>
          <Bar id="profitChart" :data="barChartData" :options="barChartOptions" />
        </div>
        <div class="chart-wrapper">
          <h2>Ventas vs Costos y Utilidad ({{ chartData.length < productProfitData.length ? 'Top 10' : 'Todos' }})</h2>
          <Bar id="salesVsCostsChart" :data="salesVsCostsChartData" :options="salesVsCostsChartOptions" />
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
            <tr class="total-row">
              <td><strong>Total</strong></td>
              <td>-</td>
              <td><strong>{{ formatCurrency(totals.ventas) }}</strong></td>
              <td><strong>{{ formatCurrency(totals.costos) }}</strong></td>
              <td><strong>{{ formatCurrency(totals.produccion) }}</strong></td>
              <td><strong>{{ formatCurrency(totals.utilidad) }}</strong></td>
              <td><strong>{{ totals.margen.toFixed(2) }}%</strong></td>
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
    LinearScale,
    LineElement,
    PointElement
  } from 'chart.js';
  import ChartDataLabels from 'chartjs-plugin-datalabels';
  import * as XLSX from 'xlsx';
  import html2canvas from 'html2canvas';
  
  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale,
    LineElement,
    PointElement,
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
      const day = ref('');
      const daysInMonth = ref([]);
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
  
      const totals = computed(() => {
        const result = productProfitData.value.reduce(
          (acc, row) => {
            acc.ventas += row.ventas;
            acc.costos += row.costos;
            acc.produccion += row.produccion;
            acc.utilidad += row.utilidad;
            acc.margen += row.margen * row.ventas;
            return acc;
          },
          { ventas: 0, costos: 0, produccion: 0, utilidad: 0, margen: 0 }
        );
        if (result.ventas > 0) {
          result.margen = (result.margen / result.ventas);
        }
        return result;
      });
  
      const chartData = computed(() => {
        if (productProfitData.value.length <= 10) {
          return productProfitData.value;
        }
        return [...productProfitData.value]
          .sort((a, b) => b.ventas - a.ventas)
          .slice(0, 10);
      });
  
      const updateDaysInMonth = () => {
        if (!year.value || !month.value) return;
        const daysInMonthMap = {
          1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
          7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        };
        if (month.value === 2 && year.value % 4 === 0 && (year.value % 100 !== 0 || year.value % 400 === 0)) {
          daysInMonthMap[2] = 29;
        }
        const numDays = daysInMonthMap[month.value] || 30;
        daysInMonth.value = Array.from({ length: numDays }, (_, i) => i + 1);
        day.value = '';
      };
  
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            updateDaysInMonth();
            fetchProducts();
            fetchData();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          updateDaysInMonth();
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
          if (day.value) params.day = day.value;
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
          if (day.value) params.day = day.value;
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
  
      const updateDaysAndFetch = () => {
        updateDaysInMonth();
        fetchProducts();
        fetchData();
      };
  
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      };
  
      const barChartData = computed(() => ({
        labels: chartData.value.map(row => row.descripcion),
        datasets: [
          {
            label: 'Margen de Utilidad (%)',
            data: chartData.value.map(row => row.margen),
            backgroundColor: 'rgba(153, 102, 255, 0.6)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1
          }
        ]
      }));
  
      const barChartOptions = computed(() => ({
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Margen (%)' }
          },
          x: { title: { display: true, text: 'Producto' } }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                const row = chartData.value[context.dataIndex];
                return [
                  `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`,
                  `Utilidad: ${formatCurrency(row.utilidad)}`
                ];
              }
            }
          },
          datalabels: {
            display: true,
            anchor: 'center',
            align: 'center',
            color: '#fff',
            font: {
              size: 13, // Ajusta este valor para cambiar el tamaño de los valores en las barras (por ejemplo, 14, 15, etc.)
              weight: 'bold'
            },
            formatter: function(value, context) {
              const row = chartData.value[context.dataIndex];
              return `${value.toFixed(2)}%\n${formatCurrency(row.utilidad)}`;
            }
          }
        }
      }));
  
      const salesVsCostsChartData = computed(() => ({
        labels: chartData.value.map(row => row.descripcion),
        datasets: [
          {
            type: 'bar',
            label: 'Ventas',
            data: chartData.value.map(row => row.ventas),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            yAxisID: 'y',
            datalabels: {
              display: !!selectedProduct.value,
              anchor: 'center',
              align: 'center',
              color: '#fff',
              font: { size: 11, weight: 'bold' },
              formatter: function(value) {
                return formatCurrency(value);
              }
            }
          },
          {
            type: 'bar',
            label: 'Costos de Producción',
            data: chartData.value.map(row => row.produccion),
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1,
            yAxisID: 'y',
            datalabels: {
              display: !!selectedProduct.value,
              anchor: 'center',
              align: 'center',
              color: '#fff',
              font: { size: 11, weight: 'bold' },
              formatter: function(value) {
                return formatCurrency(value);
              }
            }
          },
          {
            type: 'bar',
            label: 'Costos de Inventario',
            data: chartData.value.map(row => row.costos),
            backgroundColor: 'rgba(255, 206, 86, 0.6)',
            borderColor: 'rgba(255, 206, 86, 1)',
            borderWidth: 1,
            yAxisID: 'y',
            datalabels: {
              display: !!selectedProduct.value,
              anchor: 'center',
              align: 'center',
              color: '#fff',
              font: { size: 11, weight: 'bold' },
              formatter: function(value) {
                return formatCurrency(value);
              }
            }
          },
          {
            type: 'line',
            label: 'Utilidad (COP)',
            data: chartData.value.map(row => row.utilidad),
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            fill: false,
            tension: 0.1,
            yAxisID: 'y1',
            datalabels: {
              display: true,
              anchor: 'end',
              align: 'top',
              color: '#000',
              font: { size: 11, weight: 'bold' },
              formatter: function(value) {
                return formatCurrency(value);
              }
            }
          }
        ]
      }));
  
      const salesVsCostsChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { title: { display: true, text: 'Producto' } },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Valor (COP)' },
            position: 'left'
          },
          y1: {
            beginAtZero: true,
            title: { display: true, text: 'Utilidad (COP)' },
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: {
              callback: function(value) {
                return formatCurrency(value);
              }
            }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: function(context) {
                if (context.dataset.type === 'line') {
                  return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                }
                return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
              }
            }
          }
        }
      };
  
      const exportToExcel = () => {
        const data = productProfitData.value.map(row => ({
          Producto: row.descripcion,
          'Cantidad Vendida': row.cantidad_vendida,
          Ventas: row.ventas,
          Costos: row.costos,
          Producción: row.produccion,
          Utilidad: row.utilidad,
          'Margen (%)': row.margen
        }));
  
        data.push({
          Producto: 'Total',
          'Cantidad Vendida': '-',
          Ventas: totals.value.ventas,
          Costos: totals.value.costos,
          Producción: totals.value.produccion,
          Utilidad: totals.value.utilidad,
          'Margen (%)': totals.value.margen
        });
  
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Utilidad por Producto');
        XLSX.writeFile(wb, `Utilidad_por_Producto_${year.value}_${month.value}${day.value ? `_Dia${day.value}` : ''}.xlsx`);
      };
  
      const downloadChart = async (chartId) => {
        const canvas = document.getElementById(chartId);
        const link = document.createElement('a');
        link.href = await html2canvas(canvas).then(canvas => canvas.toDataURL('image/png'));
        link.download = `${chartId}_${year.value}_${month.value}${day.value ? `_Dia${day.value}` : ''}.png`;
        link.click();
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
        day,
        daysInMonth,
        selectedProduct,
        products,
        productProfitData,
        noData,
        totals,
        chartData,
        fetchData,
        updateDaysAndFetch,
        formatCurrency,
        barChartData,
        barChartOptions,
        salesVsCostsChartData,
        salesVsCostsChartOptions,
        exportToExcel,
        downloadChart
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
    flex-wrap: wrap;
  }
  
  .actions {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
  }
  
  .actions button {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .actions button:hover {
    background-color: #45a049;
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
    margin-bottom: 40px;
  }
  
  .chart-wrapper {
    margin-bottom: 60px;
    height: 400px;
  }
  
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  </style>