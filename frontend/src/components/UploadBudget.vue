<template>
  <div class="upload-budget">
    <h1>Gestión de Presupuesto de Ventas</h1>
    <div class="filters">
      <label>Año:</label>
      <select v-model="selectedYear" @change="fetchBudget">
        <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
      </select>
      <label>Estatus PDV:</label>
      <select v-model="selectedStatus" @change="fetchBudget">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
    </div>
    <div class="table-container">
      <table class="budget-table">
        <thead>
          <tr>
            <th>PDV</th>
            <th v-for="month in months" :key="month.num">{{ month.name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in budgetData" :key="index">
            <td>{{ row.pdv }}</td>
            <td v-for="month in months" :key="month.num">
              <input
                type="text"
                v-model="row[month.num]"
                @blur="formatInput(index, month.num)"
                @keydown.tab="saveOnTab(index, month.num, $event)"
                placeholder="$0"
              />
              <button
                class="delete-btn"
                @click="deleteEntry(row.pdv, month.num)"
                v-if="row[month.num] && row[month.num] !== '$0' && row[month.num] !== 0"
              >X</button>
            </td>
          </tr>
          <tr class="total-row">
            <td>Total</td>
            <td v-for="month in months" :key="month.num">{{ formatCurrency(totals[month.num]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <button @click="saveBudget">Guardar Presupuesto</button>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { mapState } from 'vuex';

export default {
  name: 'UploadBudget',
  computed: {
    ...mapState({
      token: state => state.auth.token
    })
  },
  data() {
    return {
      selectedYear: new Date().getFullYear(),
      years: Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i - 2),
      selectedStatus: 'Activo', // Por defecto Activo
      months: [
        { num: 1, name: 'Enero' }, { num: 2, name: 'Febrero' }, { num: 3, name: 'Marzo' },
        { num: 4, name: 'Abril' }, { num: 5, name: 'Mayo' }, { num: 6, name: 'Junio' },
        { num: 7, name: 'Julio' }, { num: 8, name: 'Agosto' }, { num: 9, name: 'Septiembre' },
        { num: 10, name: 'Octubre' }, { num: 11, name: 'Noviembre' }, { num: 12, name: 'Diciembre' }
      ],
      budgetData: [],
      totals: {}
    };
  },
  methods: {
    async fetchBudget() {
      try {
        const response = await axios.get('/budget/sales', {
          params: { year: this.selectedYear, status: this.selectedStatus }
        });
        this.budgetData = response.data.data.map(row => ({
          ...row,
          ...Object.fromEntries(
            Object.entries(row).map(([key, value]) => 
              key !== 'pdv' && value ? [key, this.formatCurrency(value)] : [key, value]
            )
          )
        }));
        this.totals = response.data.totals;
        this.updateTotals();
      } catch (error) {
        console.error('Error fetching budget:', error);
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          this.$router.push('/login');
        }
      }
    },
    formatInput(rowIndex, month) {
      let value = this.budgetData[rowIndex][month];
      if (value && typeof value === 'string') {
        // Limpiar completamente antes de convertir
        const cleanedValue = value.replace(/[^0-9]/g, ''); // Solo números, sin puntos ni otros caracteres
        if (!isNaN(cleanedValue) && cleanedValue !== '') {
          const numValue = parseFloat(cleanedValue);
          this.budgetData[rowIndex][month] = this.formatCurrency(numValue);
          this.updateTotals();
        }
      }
    },
    formatCurrency(value) {
      return value ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value) : '$0';
    },
    updateTotals() {
      this.totals = this.months.reduce((acc, month) => {
        acc[month.num] = this.budgetData.reduce((sum, row) => {
          const val = row[month.num] ? parseFloat(row[month.num].toString().replace(/[^0-9]/g, '')) || 0 : 0;
          return sum + val;
        }, 0);
        return acc;
      }, {});
    },
    async saveBudget() {
      try {
        const cleanedData = this.budgetData.map(row => {
          const cleanedRow = { pdv: row.pdv };
          this.months.forEach(month => {
            if (row[month.num] && row[month.num] !== '$0' && row[month.num] !== 0) {
              const rawValue = row[month.num].toString().replace(/[^0-9]/g, ''); // Solo números
              cleanedRow[month.num] = parseFloat(rawValue);
            }
          });
          return cleanedRow;
        });
        console.log('Datos enviados:', cleanedData);
        await axios.post('/budget/sales', {
          year: this.selectedYear,
          budget: cleanedData
        });
        alert('Presupuesto guardado exitosamente');
        this.fetchBudget();
      } catch (error) {
        console.error('Error saving budget:', error);
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          this.$router.push('/login');
        } else {
          alert('Error al guardar el presupuesto');
        }
      }
    },
    async saveOnTab(rowIndex, month, event) {
      event.preventDefault();
      await this.formatInput(rowIndex, month);
      await this.saveBudget();
    },
    async deleteEntry(pdv, month) {
      if (confirm(`¿Eliminar el presupuesto de ${pdv} para ${this.months[month - 1].name} ${this.selectedYear}?`)) {
        try {
          await axios.delete('/budget/sales/delete', {
            data: { year: this.selectedYear, pdv, month }
          });
          this.fetchBudget();
        } catch (error) {
          console.error('Error deleting budget:', error);
          if (error.response && error.response.status === 401) {
            console.log('No autorizado, redirigiendo al login');
            this.$router.push('/login');
          } else {
            alert('Error al eliminar el presupuesto');
          }
        }
      }
    },
  },
  mounted() {
    if (this.token) {
      this.fetchBudget();
    } else {
      console.log('No hay token, redirigiendo al login');
      this.$router.push('/login');
    }
  },
};
</script>

<style scoped>
.upload-budget {
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
  overflow-x: auto; /* Barra de desplazamiento horizontal */
  margin-bottom: 20px;
}
.budget-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10px; /* Tamaño de letra más pequeño */
}
.budget-table th, .budget-table td {
  border: 1px solid #ddd;
  padding: 4px; /* Reducir padding */
  text-align: center;
}
.budget-table th {
  background-color: #f2f2f2;
  font-size: 10px; /* Encabezados más pequeños */
}
.budget-table td {
  max-width: 120px; /* Limitar ancho de celdas */
  white-space: nowrap; /* Evitar salto de línea */
}
.budget-table input {
  width: 70%;
  padding: 2px; /* Reducir padding del input */
  border: none;
  text-align: right;
  font-size: 10px; /* Tamaño de fuente más pequeño */
}
.total-row {
  font-weight: bold;
  background-color: #f9f9f9;
}
button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  cursor: pointer;
}
button:hover {
  background-color: #2c3e50;
}
.delete-btn {
  padding: 1px 4px; /* Botón más pequeño */
  background-color: #ff4444;
  margin-left: 5px;
  font-size: 10px; /* Tamaño de fuente más pequeño */
}
.delete-btn:hover {
  background-color: #cc0000;
}
</style>