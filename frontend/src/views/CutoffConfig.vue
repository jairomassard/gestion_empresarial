<template>
  <div class="cutoff-config">
    <h1>Configuración del Mes de Corte</h1>
    <p>Defina el mes de corte para separar los datos históricos (ventahistorica) de los datos diarios (ventahistoricahora).</p>
    <div class="form-container">
      <div class="form-group" :class="{ 'has-error': errors.cutoffYear }">
        <label>Año:</label>
        <input
          type="number"
          v-model.number="cutoffYear"
          min="2000"
          max="2100"
          placeholder="Ej. 2025"
          @input="clearError('cutoffYear')"
        />
        <span class="error-message" v-if="errors.cutoffYear">{{ errors.cutoffYear }}</span>
      </div>
      <div class="form-group" :class="{ 'has-error': errors.cutoffMonth }">
        <label>Mes:</label>
        <select v-model.number="cutoffMonth" @change="clearError('cutoffMonth')">
          <option :value="null" disabled>Seleccione un mes</option>
          <option v-for="(month, index) in months" :key="index" :value="index + 1">
            {{ month }}
          </option>
        </select>
        <span class="error-message" v-if="errors.cutoffMonth">{{ errors.cutoffMonth }}</span>
      </div>
      <button
        @click="saveConfig"
        :disabled="isSaving || !isFormValid"
        class="save-button"
      >
        {{ isSaving ? 'Guardando...' : 'Guardar' }}
      </button>
    </div>
    <p class="message" :class="{ error: messageIsError }">{{ message }}</p>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { useStore } from 'vuex';

export default {
  name: 'CutoffConfig',
  setup() {
    return { store: useStore() };
  },
  data() {
    return {
      cutoffYear: null,
      cutoffMonth: null,
      months: [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
      ],
      isSaving: false,
      message: '',
      messageIsError: false,
      errors: {
        cutoffYear: '',
        cutoffMonth: ''
      }
    };
  },
  computed: {
    isFormValid() {
      return this.cutoffYear >= 2000 && this.cutoffYear <= 2100 && this.cutoffMonth >= 1 && this.cutoffMonth <= 12;
    }
  },
  methods: {
    async fetchConfig() {
      try {
        const response = await axios.get('/config/cutoff');
        const { CutoffYear, CutoffMonth } = response.data;
        if (CutoffYear === null && CutoffMonth === null) {
          this.message = 'No hay configuración de cutoff definida. Ingrese un año y mes para continuar.';
          this.messageIsError = false;
          this.cutoffYear = null;
          this.cutoffMonth = null;
        } else {
          this.cutoffYear = CutoffYear;
          this.cutoffMonth = CutoffMonth;
          this.message = '';
        }
      } catch (error) {
        console.error('Error fetching config:', error);
        this.message = error.response?.data?.error || 'Error al cargar la configuración';
        this.messageIsError = true;
        if (error.response?.status === 401) {
          this.$router.push('/login');
        }
      }
    },
    async saveConfig() {
      this.errors = { cutoffYear: '', cutoffMonth: '' };
      if (!this.cutoffYear) {
        this.errors.cutoffYear = 'El año es requerido';
      } else if (this.cutoffYear < 2000 || this.cutoffYear > 2100) {
        this.errors.cutoffYear = 'El año debe estar entre 2000 y 2100';
      }
      if (!this.cutoffMonth) {
        this.errors.cutoffMonth = 'El mes es requerido';
      }
      if (this.errors.cutoffYear || this.errors.cutoffMonth) {
        this.message = 'Por favor, corrija los errores en el formulario';
        this.messageIsError = true;
        return;
      }

      this.isSaving = true;
      this.message = '';
      this.messageIsError = false;
      try {
        await axios.post('/config/cutoff', {
          CutoffYear: this.cutoffYear,
          CutoffMonth: this.cutoffMonth
        });
        this.message = 'Configuración guardada con éxito';
        this.messageIsError = false;
      } catch (error) {
        console.error('Error saving config:', error);
        this.message = error.response?.data?.error || 'Error al guardar la configuración';
        this.messageIsError = true;
        if (error.response?.status === 401) {
          this.$router.push('/login');
        }
      } finally {
        this.isSaving = false;
      }
    },
    clearError(field) {
      this.errors[field] = '';
      if (!this.errors.cutoffYear && !this.errors.cutoffMonth) {
        this.message = '';
        this.messageIsError = false;
      }
    }
  },
  mounted() {
    if (!this.store.getters.isAuthenticated) {
      this.$router.push('/login');
    } else if (!this.store.getters.hasPermission('parametrizacion', 'cutoff', 'editar')) {
      this.$router.push('/');
    } else {
      this.fetchConfig();
    }
  }
};
</script>

<style scoped>
.cutoff-config {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  font-size: 1.8rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

p {
  font-size: 1rem;
  color: #34495e;
  margin-bottom: 20px;
}

.form-container {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-group.has-error input,
.form-group.has-error select {
  border-color: red;
}

label {
  font-weight: bold;
  color: #2c3e50;
  width: 100px;
}

input, select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.error-message {
  color: red;
  font-size: 0.9rem;
  margin-top: 5px;
  display: block;
}

.save-button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.save-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.save-button:hover:not(:disabled) {
  background-color: #2c3e50;
}

.message {
  margin-top: 15px;
  font-weight: bold;
}

.message.error {
  color: red;
}
</style>
