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
            <tr class="total-row">
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
    </div>
  </template>
  
  <script>
  import axios from '@/api/axios';
  
  export default {
    name: 'MonthlyPerformance',
    data() {
      return {
        year: 2025,
        years: Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i - 2),
        month: 2, // Febrero por defecto
        months: [
          { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
          { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
          { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
          { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
        ],
        status: 'Activo',
        dashboardData: [],
        totals: {}
      };
    },
    methods: {
      async fetchData() {
        try {
          const response = await axios.get('/dashboard/monthly-performance', {
            params: { year: this.year, month: this.month, status: this.status }
          });
          this.dashboardData = response.data.data;
          this.totals = response.data.totals;
        } catch (error) {
          console.error('Error fetching dashboard data:', error);
        }
      },
      formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
      },
      formatPercent(value) {
        return new Intl.NumberFormat('es-CO', { style: 'percent', minimumFractionDigits: 2 }).format(value / 100);
      }
    },
    mounted() {
      this.fetchData();
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