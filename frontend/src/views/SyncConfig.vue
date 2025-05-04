<template>
    <div class="sync-config">
      <h1>Configuración de Sincronización de Módulos</h1>
      <p>Configure las opciones de sincronización entre los módulos de análisis, inventario y producción.</p>
      <div class="form-container">
        <div class="form-group">
          <label>Sincronizar con Inventario:</label>
          <input
            type="checkbox"
            v-model="config.sync_analisis_inventario"
          />
        </div>
        <div class="form-group">
          <label>Sincronizar con Producción:</label>
          <input
            type="checkbox"
            v-model="config.sync_analisis_produccion"
          />
        </div>
        <button
          @click="saveConfig"
          :disabled="isSaving"
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
    name: 'SyncConfig',
    setup() {
      return { store: useStore() };
    },
    data() {
      return {
        config: {
          sync_analisis_inventario: false,
          sync_analisis_produccion: false
        },
        isSaving: false,
        message: '',
        messageIsError: false
      };
    },
    methods: {
      async fetchConfig() {
        try {
          const response = await axios.get('/config/sync');
          const { sync_analisis_inventario, sync_analisis_produccion } = response.data;
          this.config = {
            sync_analisis_inventario: sync_analisis_inventario || false,
            sync_analisis_produccion: sync_analisis_produccion || false
          };
          this.message = '';
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
        this.message = '';
        this.messageIsError = false;
        this.isSaving = true;
        try {
          await axios.post('/config/sync', this.config);
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
      }
    },
    mounted() {
      if (!this.store.getters.isAuthenticated) {
        this.$router.push('/login');
      } else if (!this.store.getters.hasPermission('parametrizacion', 'sync_config', 'editar')) {
        this.$router.push('/');
      } else {
        this.fetchConfig();
      }
    }
  };
  </script>
  
  <style scoped>
  .sync-config {
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
  
  label {
    font-weight: bold;
    color: #2c3e50;
    width: 200px;
  }
  
  input[type="checkbox"] {
    width: 20px;
    height: 20px;
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