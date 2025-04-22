<template>
  <div class="historical-sales">
    <h1>Ventas Históricas</h1>
    <div class="filters">
      <label>Año:</label>
      <select v-model="selectedYear" @change="fetchData">
        <option :value="null">Todos</option>
        <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
      </select>

      <label>Mes:</label>
      <select v-model="selectedMonth" @change="fetchData">
        <option :value="null">Todos</option>
        <option v-for="(month, index) in months" :key="index" :value="index + 1">{{ month }}</option>
      </select>

      <label>Estatus PDV:</label>
      <select v-model="selectedStatus" @change="fetchData">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>

      <!-- Nuevo filtro por PDV -->
      <label>PDV:</label>
      <select v-model="selectedPDV" @change="fetchData">
        <option value="Todos">Todos</option>
        <option v-for="pdv in pdvList" :key="pdv" :value="pdv">{{ pdv }}</option>
      </select>
    </div>

    <!-- Gráfico (movido arriba) -->
    <div class="chart-container">
      <canvas id="salesChart"></canvas>
    </div>

    <!-- Tabla -->
    <vue-good-table :columns="pivotColumns" :rows="filteredPivotData" />
  </div>
</template>

<script>
import axios from '@/api/axios';
import { VueGoodTable } from 'vue-good-table-next';
import 'vue-good-table-next/dist/vue-good-table-next.css';
import Chart from 'chart.js/auto';


export default {
  name: 'HistoricalSales',
  components: { VueGoodTable },
  data() {
    return {
      selectedYear: null,
      selectedMonth: null,
      selectedStatus: 'Activo',
      selectedPDV: 'Todos',
      years: Array.from({ length: 2025 - 2018 + 1 }, (_, i) => 2018 + i),
      months: [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
      ],
      pdvList: [],
      pivotColumns: [],
      pivotData: [],
      filteredPivotData: [],
      chart: null,
      // Lista de colores predefinidos
      chartColors: [
        'rgba(75, 192, 192, 0.5)', // Turquesa
        'rgba(255, 99, 132, 0.5)', // Rosa
        'rgba(54, 162, 235, 0.5)', // Azul
        'rgba(255, 206, 86, 0.5)', // Amarillo
        'rgba(153, 102, 255, 0.5)', // Púrpura
        'rgba(255, 159, 64, 0.5)', // Naranja
        'rgba(0, 128, 0, 0.5)'     // Verde
      ],
      borderColors: [
        'rgba(75, 192, 192, 0.5)', // Turquesa
        'rgba(255, 99, 132, 0.5)', // Rosa
        'rgba(54, 162, 235, 0.5)', // Azul
        'rgba(255, 206, 86, 0.5)', // Amarillo
        'rgba(153, 102, 255, 0.5)', // Púrpura
        'rgba(255, 159, 64, 0.5)', // Naranja
        'rgba(0, 128, 0, 0.5)'     // Verde
      ]
    };
  },
  methods: {
    async fetchData() {
      console.log('Token en el store:', this.$store.state.auth.token);
      try {
        const params = {};
        if (this.selectedYear) params.year = this.selectedYear;
        if (this.selectedMonth) params.month = this.selectedMonth;
        params.status = this.selectedStatus;
        if (this.selectedPDV !== 'Todos') params.pdv = this.selectedPDV; // Enviar PDV al backend

        const response = await axios.get('/dashboard/historical_sales', { params });
        const data = response.data;

        // Actualizar columnas de la tabla
        this.pivotColumns = [
          { label: 'PDV', field: 'pdv' },
          ...data.years.map(year => ({
            label: year.toString(),
            field: year.toString(),
            type: 'number',
            formatFn: this.formatCurrency
          }))
        ];

        // Actualizar datos de la tabla
        this.pivotData = data.data;

        // Actualizar lista de PDVs
        this.pdvList = [...new Set(data.data.filter(row => row.pdv !== 'Total').map(row => row.pdv))].sort();

        // Filtrar datos para la tabla (aunque el backend ya filtra, esto es por si el backend no lo hace)
        this.updateFilteredData();

        // Actualizar gráfico
        this.updateChart(data);
      } catch (error) {
        console.error('Error fetching data:', error);
        this.pivotData = [];
        this.filteredPivotData = [];
        this.pdvList = [];
      }
    },
    updateFilteredData() {
      // Si el backend ya filtra por PDV, esto no será necesario, pero lo dejamos por seguridad
      if (this.selectedPDV === 'Todos') {
        this.filteredPivotData = this.pivotData;
      } else {
        this.filteredPivotData = this.pivotData.filter(row => row.pdv === this.selectedPDV || row.pdv === 'Total');
      }
    },
    formatCurrency(value) {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(value);
    },
    updateChart(data) {
      const ctx = document.getElementById('salesChart').getContext('2d');
      const labels = data.data.filter(row => row.pdv !== 'Total').map(row => row.pdv);
      const years = data.years;
      const datasets = years.map((year, index) => ({
        label: year.toString(),
        data: data.data.filter(row => row.pdv !== 'Total').map(row => row[year] || 0),
        backgroundColor: this.chartColors[index % this.chartColors.length], // Cicla los colores si hay más años que colores
        borderColor: this.borderColors[index % this.borderColors.length],
        borderWidth: 1
      }));

      if (this.chart) {
        this.chart.destroy();
      }

      this.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: value => this.formatCurrency(value)
              }
            }
          },
          plugins: {
            legend: { display: true },
            tooltip: {
              callbacks: {
                label: context => `${context.dataset.label}: ${this.formatCurrency(context.raw)}`
              }
            },
            datalabels: {
              display: false,
            },
          }
        }
      });
    }
  },
  mounted() {
    if (this.$store.state.auth.token) {
      this.fetchData();
    } else {
      console.log('No hay token, redirigiendo al login');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.historical-sales {
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
  margin-right: 20px;
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.chart-container {
  margin-bottom: 80px; /* Espaciado entre el gráfico y la tabla */
  max-width: 1500px; /* Aumentar el ancho máximo del gráfico */
  height: 500px; /* Aumentar la altura del gráfico */
  margin-left: auto;
  margin-right: auto;
}

.vgt-table {
  font-size: 12px;
}

.vgt-table th,
.vgt-table td {
  padding: 4px;
  vertical-align: middle;
}

.vgt-table th {
  font-size: 11px;
}

.vgt-table td {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>