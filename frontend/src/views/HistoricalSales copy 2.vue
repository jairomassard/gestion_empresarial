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
    </div>

    <vue-good-table :columns="pivotColumns" :rows="pivotData" />
    <div class="chart-container">
      <canvas id="salesChart"></canvas>
    </div>
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
      years: Array.from({ length: 2025 - 2018 + 1 }, (_, i) => 2018 + i),
      months: [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
      ],
      pivotColumns: [],
      pivotData: [],
      chart: null
    };
  },
  methods: {
    async fetchData() {
      console.log('Token en el store:', this.$store.state.auth.token); // Depuración
      try {
        const params = {};
        if (this.selectedYear) params.year = this.selectedYear;
        if (this.selectedMonth) params.month = this.selectedMonth;
        params.status = this.selectedStatus;

        const response = await axios.get('/dashboard/historical_sales', { params });
        const data = response.data;

        this.pivotColumns = [
          { label: 'PDV', field: 'pdv' },
          ...data.years.map(year => ({
            label: year.toString(),
            field: year.toString(),
            type: 'number',
            formatFn: this.formatCurrency
          }))
        ];
        this.pivotData = data.data;

        this.updateChart(data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    },
    formatCurrency(value) {
      return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(value);
    },
    updateChart(data) {
      const ctx = document.getElementById('salesChart').getContext('2d');
      const labels = data.data.filter(row => row.pdv !== 'Total').map(row => row.pdv);
      const years = data.years;
      const datasets = years.map(year => ({
        label: year.toString(),
        data: data.data.filter(row => row.pdv !== 'Total').map(row => row[year] || 0),
        backgroundColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 0.5)`,
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`,
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
            }
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
}
label {
  margin-right: 10px;
}
select {
  margin-right: 20px;
  padding: 5px;
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
.chart-container {
  margin-top: 20px;
  max-width: 1000px;
  margin-left: auto;
  margin-right: auto;
}
</style>