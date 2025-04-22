<template>
    <div class="accumulated-sales-by-pdv">
      <h1>Venta Acumulada por PDV - {{ months[month - 1].name }} {{ year }}</h1>
      <div class="filters">
        <label>Año:</label>
        <select v-model="year" @change="updateEndDateOptions; fetchData">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <label>Mes:</label>
        <select v-model="month" @change="updateEndDateOptions; fetchData">
          <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
        </select>
        <label>Día Final:</label>
        <select v-model="endDate" @change="fetchData">
          <option v-for="day in availableDays" :key="day" :value="day">{{ day.split('-')[2] }}</option>
        </select>
        <label>Estatus PDV:</label>
        <select v-model="status" @change="fetchPDVs">
          <option value="Todos">Todos</option>
          <option value="Activo">Activo</option>
          <option value="Inactivo">Inactivo</option>
        </select>
        <label>Punto de Venta:</label>
        <select v-model="pdv" @change="fetchData">
          <option v-for="p in pdvs" :key="p" :value="p">{{ p }}</option>
        </select>
        
      </div>
  
      <!-- Botón para exportar -->
      <div class="sort-buttons">
        <button @click="exportToExcel" :disabled="noData">Exportar a Excel</button>
      </div>
  
      <!-- Mensaje si no hay datos -->
      <div v-if="noData" class="no-data-message">
        No hay datos disponibles para el mes, año y PDV seleccionados.
      </div>
  
      <!-- Tabla de Métricas -->
      <div v-else class="table-container">
        <table class="sales-table">
          <thead>
            <tr>
              <th>Métrica</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Venta Acumulada</td>
              <td>{{ formatCurrency(data.venta_acumulada) }}</td>
            </tr>
            <tr>
              <td>Venta Proyectada</td>
              <td>{{ formatCurrency(data.venta_proyectada) }}</td>
            </tr>
            <tr>
              <td>Presupuesto</td>
              <td>{{ formatCurrency(data.presupuesto) }}</td>
            </tr>
            <tr>
              <td>Cumplimiento a la Fecha</td>
              <td>{{ formatCurrency(data.cumplimiento_a_la_fecha) }}</td>
            </tr>
            <tr>
              <td>% Cumplimiento</td>
              <td>{{ data.cumplimiento_porcentual }}% {{ data.cumplimiento_icono }}</td>
            </tr>
            <tr>
              <td>Saldo para Cumplir</td>
              <td :class="data.saldo_para_cumplir >= 0 ? 'positive' : 'negative'">
                {{ formatCurrency(data.saldo_para_cumplir) }}
              </td>
            </tr>
            <tr>
              <td>Venta mes {{ months[month - 1].name }} del Año Anterior</td>
              <td>{{ formatCurrency(data.venta_ano_anterior) }}</td>
            </tr>
            <tr>
              <td>Crecimiento (%)</td>
              <td :class="data.crecimiento_porcentual >= 0 ? 'positive' : 'negative'">
                {{ data.crecimiento_porcentual }}%
              </td>
            </tr>
            <tr>
              <td>Crecimiento ($)</td>
              <td :class="data.crecimiento_valor >= 0 ? 'positive' : 'negative'">
                {{ formatCurrency(data.crecimiento_valor) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Gráficos -->
      <div v-if="!noData" class="charts-container">
        <!-- Gráficos de Productos (uno al lado del otro) -->
        <div class="chart-row">
          <div class="chart-wrapper">
            <h2>Top 5 Productos Más Vendidos</h2>
            <Bar :data="productChartData" :options="productChartOptions" />
          </div>
          <div class="chart-wrapper">
            <h2>Distribución de Ventas (Top 5 Productos)</h2>
            <Doughnut :data="productDoughnutChartData" :options="doughnutChartOptions" />
          </div>
        </div>
  
        <!-- Gráficos de Asesores (uno al lado del otro) -->
        <div class="chart-row">
          <div class="chart-wrapper">
            <h2>Top 5 Asesores Más Vendidos</h2>
            <Bar :data="sellerChartData" :options="sellerChartOptions" />
          </div>
          <div class="chart-wrapper">
            <h2>Distribución de Ventas (Top 5 Asesores)</h2>
            <Doughnut :data="sellerDoughnutChartData" :options="doughnutChartOptions" />
          </div>
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
    ArcElement,
  } from 'chart.js';
  import * as XLSX from 'xlsx';
  import { saveAs } from 'file-saver';
  
  // Registrar los componentes de Chart.js
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);
  
  export default {
    name: 'AccumulatedSalesByPDV',
    components: {
      Bar,
      Doughnut,
    },
    setup() {
      // Datos reactivos
      const year = ref(null);
      const years = ref([]);
      const currentDate = new Date();
      const currentYear = currentDate.getFullYear();
      const currentMonth = currentDate.getMonth() + 1;
      const month = ref(currentMonth);
      const months = ref([
        { num: 1, name: 'Enero' },
        { num: 2, name: 'Febrero' },
        { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' },
        { num: 5, name: 'Mayo' },
        { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' },
        { num: 8, name: 'Agosto' },
        { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' },
        { num: 11, name: 'Noviembre' },
        { num: 12, name: 'Diciembre' },
      ]);
      const status = ref('Activo'); // Filtro de estatus por defecto
      const pdv = ref('');
      const pdvs = ref([]);
      const endDate = ref('');
      const availableDays = ref([]);
      const data = ref(null);
  
      // Computed para determinar si no hay datos
      const noData = computed(() => {
        return !data.value || (data.value.venta_acumulada === 0 && data.value.venta_proyectada === 0);
      });
  
      // Computed para los datos del gráfico de barras de productos
      const productChartData = computed(() => {
        if (!data.value || !data.value.top_products) return { labels: [], datasets: [] };
  
        const labels = data.value.top_products.map(item => item.product);
        const values = data.value.top_products.map(item => item.sales);
  
        return {
          labels: labels,
          datasets: [
            {
              label: 'Ventas (COP)',
              data: values,
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1,
            },
          ],
        };
      });
  
      const productChartOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Ventas (COP)',
            },
            ticks: {
              callback: function (value) {
                return new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                }).format(value);
              },
            },
          },
          y: {
            title: {
              display: true,
              text: 'Producto',
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                }).format(context.parsed.x);
                return label;
              },
            },
          },
        },
      };
  
      // Computed para el gráfico de dona de productos
      const productDoughnutChartData = computed(() => {
        if (!data.value || !data.value.top_products) return { labels: [], datasets: [] };
  
        const colors = [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ];
        const borderColors = colors.map(color => color.replace('0.6', '1'));
  
        return {
          labels: data.value.top_products.map(item => item.product),
          datasets: [
            {
              label: 'Distribución de Ventas',
              data: data.value.top_products.map(item => item.sales),
              backgroundColor: colors,
              borderColor: borderColors,
              borderWidth: 1,
            },
          ],
        };
      });
  
      // Computed para los datos del gráfico de barras de asesores
      const sellerChartData = computed(() => {
        if (!data.value || !data.value.top_sellers) return { labels: [], datasets: [] };
  
        const labels = data.value.top_sellers.map(item => item.seller);
        const values = data.value.top_sellers.map(item => item.sales);
  
        return {
          labels: labels,
          datasets: [
            {
              label: 'Ventas (COP)',
              data: values,
              backgroundColor: 'rgba(255, 159, 64, 0.6)',
              borderColor: 'rgba(255, 159, 64, 1)',
              borderWidth: 1,
            },
          ],
        };
      });
  
      const sellerChartOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Ventas (COP)',
            },
            ticks: {
              callback: function (value) {
                return new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                }).format(value);
              },
            },
          },
          y: {
            title: {
              display: true,
              text: 'Asesor',
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                }).format(context.parsed.x);
                return label;
              },
            },
          },
        },
      };
  
      // Computed para el gráfico de dona de asesores
      const sellerDoughnutChartData = computed(() => {
        if (!data.value || !data.value.top_sellers) return { labels: [], datasets: [] };
  
        const colors = [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ];
        const borderColors = colors.map(color => color.replace('0.6', '1'));
  
        return {
          labels: data.value.top_sellers.map(item => item.seller),
          datasets: [
            {
              label: 'Distribución de Ventas',
              data: data.value.top_sellers.map(item => item.sales),
              backgroundColor: colors,
              borderColor: borderColors,
              borderWidth: 1,
            },
          ],
        };
      });
  
      const doughnutChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right',
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.label || '';
                if (label) {
                  label += ': ';
                }
                label += new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                }).format(context.parsed);
                return label;
              },
            },
          },
        },
      };
  
      // Obtener los años disponibles
      const fetchAvailableYears = async () => {
        try {
          const response = await axios.get('/available-years');
          years.value = response.data.years || [];
          if (years.value.length > 0) {
            year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
            updateEndDateOptions();
            fetchPDVs();
          }
        } catch (error) {
          console.error('Error fetching available years:', error);
          years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
          year.value = currentYear;
          updateEndDateOptions();
          fetchPDVs();
        }
      };
  
      // Obtener los PDVs disponibles con filtro de estatus
      const fetchPDVs = async () => {
        try {
          const response = await axios.get('/dashboard/historical_sales', {
            params: { status: status.value },
          });
          pdvs.value = response.data.data
            .filter(row => row.pdv !== 'Total')
            .map(row => row.pdv);
          pdv.value = pdvs.value[0] || '';
          fetchData();
        } catch (error) {
          console.error('Error fetching PDVs:', error);
          pdvs.value = [];
          pdv.value = '';
        }
      };
  
      // Actualizar las opciones de fecha final según el año y mes seleccionados
      const updateEndDateOptions = () => {
        if (!year.value || !month.value) return;
  
        const daysInMonth = new Date(year.value, month.value, 0).getDate();
        availableDays.value = Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          return `${year.value}-${String(month.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        });
  
        // Seleccionar el último día del mes por defecto, o el día actual si es el mes actual
        const today = new Date();
        if (year.value === today.getFullYear() && month.value === today.getMonth() + 1) {
          const todayStr = `${year.value}-${String(month.value).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
          endDate.value = availableDays.value.includes(todayStr) ? todayStr : availableDays.value[availableDays.value.length - 1];
        } else {
          endDate.value = availableDays.value[availableDays.value.length - 1];
        }
  
        // Forzar la actualización de los datos después de cambiar el mes o año
        fetchData();
      };
  
      // Obtener los datos del dashboard
      const fetchData = async () => {
        if (!year.value || !month.value || !pdv.value || !endDate.value) return;
  
        // Validar que endDate esté dentro del mes y año seleccionados
        const [endYear, endMonth] = endDate.value.split('-').map(Number);
        if (endYear !== year.value || endMonth !== month.value) {
          console.warn('endDate does not match selected year and month, updating endDate...');
          updateEndDateOptions();
          return;
        }
  
        try {
          const response = await axios.get('/dashboard/accumulated-sales-by-pdv', {
            params: {
              year: year.value,
              month: month.value,
              pdv: pdv.value,
              end_date: endDate.value,
              status: status.value,
            },
          });
          data.value = response.data;
        } catch (error) {
          console.error('Error fetching accumulated sales data:', error);
          data.value = null;
        }
      };
  
      // Formatear moneda
      const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          minimumFractionDigits: 0,
        }).format(value);
      };
  
      // Exportar a Excel
        const exportToExcel = () => {
        if (!data.value) return;

        // Crear los datos de los filtros
        const filtersData = [
            { Filtro: 'Año', Valor: year.value },
            { Filtro: 'Mes', Valor: months.value[month.value - 1].name },
            { Filtro: 'Punto de Venta (PDV)', Valor: pdv.value },
            { Filtro: 'Fecha Final', Valor: endDate.value },
            { Filtro: 'Estatus PDV', Valor: status.value },
        ];

        // Datos de la tabla
        const tableData = [
            { Métrica: 'Venta Acumulada', Valor: data.value.venta_acumulada },
            { Métrica: 'Venta Proyectada', Valor: data.value.venta_proyectada },
            { Métrica: 'Presupuesto', Valor: data.value.presupuesto },
            { Métrica: 'Cumplimiento a la Fecha', Valor: data.value.cumplimiento_a_la_fecha },
            { Métrica: '% Cumplimiento', Valor: `${data.value.cumplimiento_porcentual}%` },
            { Métrica: 'Saldo para Cumplir', Valor: data.value.saldo_para_cumplir },
            { Métrica: `Venta mes ${months.value[month.value - 1].name} del Año Anterior`, Valor: data.value.venta_ano_anterior },
            { Métrica: 'Crecimiento (%)', Valor: `${data.value.crecimiento_porcentual}%` },
            { Métrica: 'Crecimiento ($)', Valor: data.value.crecimiento_valor },
        ];

        // Agregar los datos de Top 5 Productos y Asesores
        tableData.push({}, { Métrica: 'Top 5 Productos Más Vendidos', Valor: '' });
        data.value.top_products.forEach((item, index) => {
            tableData.push({ Métrica: `Producto ${index + 1}`, Valor: `${item.product}: ${formatCurrency(item.sales)}` });
        });

        tableData.push({}, { Métrica: 'Top 5 Asesores Más Vendidos', Valor: '' });
        data.value.top_sellers.forEach((item, index) => {
            tableData.push({ Métrica: `Asesor ${index + 1}`, Valor: `${item.seller}: ${formatCurrency(item.sales)}` });
        });

        // Crear una hoja de Excel vacía
        const ws = XLSX.utils.json_to_sheet([]);

        // Agregar los filtros en las primeras filas (a partir de la fila 1, columna A)
        XLSX.utils.sheet_add_json(ws, filtersData, { origin: 'A1', skipHeader: false });

        // Dejar una fila vacía después de los filtros
        const filtersRowCount = filtersData.length;
        const emptyRow = filtersRowCount + 2; // Fila vacía después de los filtros

        // Agregar los datos de la tabla después de la fila vacía
        XLSX.utils.sheet_add_json(ws, tableData, { origin: `A${emptyRow}`, skipHeader: false });

        // Crear el libro de Excel y exportar
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Venta Acumulada por PDV');
        const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/octet-stream' });
        saveAs(blob, `Venta_Acumulada_${pdv.value}_${months.value[month.value - 1].name}_${year.value}.xlsx`);
      };
  
      // Cargar datos iniciales
      onMounted(() => {
        fetchAvailableYears();
      });
  
      return {
        year,
        years,
        month,
        months,
        status,
        pdv,
        pdvs,
        endDate,
        availableDays,
        data,
        noData,
        productChartData,
        productChartOptions,
        productDoughnutChartData,
        sellerChartData,
        sellerChartOptions,
        sellerDoughnutChartData,
        doughnutChartOptions,
        fetchAvailableYears,
        fetchPDVs,
        updateEndDateOptions,
        fetchData,
        formatCurrency,
        exportToExcel,
      };
    },
  };
  </script>
  
  <style scoped>
  .accumulated-sales-by-pdv {
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
  .sort-buttons button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
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
    max-width: 200px;
    white-space: normal;
    word-wrap: break-word;
  }
  .sales-table td:first-child {
    text-align: left;
  }
  .positive {
    color: green;
  }
  .negative {
    color: red;
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
  .chart-row {
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
  }
  .chart-wrapper {
    flex: 1;
    margin: 0 10px;
    height: 300px;
    max-width: 500px;
  }
  .chart-wrapper h2 {
    text-align: center;
    margin-bottom: 10px;
    font-size: 16px;
  }
  </style>

