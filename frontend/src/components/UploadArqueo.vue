<template>
  <div class="upload-arqueo">
    <h2>Cargar Arqueo de Caja</h2>
    <div class="instructions">
      <p>Suba un archivo Excel (.xlsx) con los datos de arqueo de caja. Descargue la plantilla para usar el formato correcto.</p>
      <p><strong>Columnas requeridas (en la primera fila):</strong> AN 3, Fecha, Z, Total, BONOS, EFECTIVO, RECIBO BANCARIO, TARJETA DEBITO, TRANSFERENCIA BANCARIA, VALE</p>
    </div>
    <div class="form-group">
      <button @click="downloadTemplate">Descargar Plantilla</button>
    </div>
    <div class="form-group">
      <input type="file" ref="fileInput" @change="handleFileUpload" accept=".xlsx" />
      <button @click="uploadFile" :disabled="!file || isUploading">
        {{ isUploading ? 'Subiendo...' : 'Subir' }}
      </button>
      <div v-if="isUploading" class="spinner">Cargando...</div>
    </div>
    <p class="message" :class="{ error: messageIsError }">{{ message }}</p>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { mapState } from 'vuex';
import * as XLSX from 'xlsx';

export default {
  name: 'UploadArqueo',
  data() {
    return {
      file: null,
      message: '',
      messageIsError: false,
      isUploading: false
    };
  },
  computed: {
    ...mapState({
      token: state => state.auth.token
    })
  },
  methods: {
    handleFileUpload(event) {
      this.file = event.target.files[0];
      this.message = '';
      this.messageIsError = false;
    },
    async uploadFile() {
      if (!this.file) {
        this.message = 'Por favor, seleccione un archivo';
        this.messageIsError = true;
        return;
      }

      this.isUploading = true;
      this.message = '';
      this.messageIsError = false;

      const formData = new FormData();
      formData.append('file', this.file);

      try {
        const response = await axios.post('/upload_arqueo', formData, {
          headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${this.token}` }
        });
        console.log('Respuesta del backend:', response);
        this.message = response.data.message || 'Cargado con éxito';
        this.messageIsError = false;
        this.file = null;
        this.$refs.fileInput.value = '';
      } catch (error) {
        console.error('Error en la solicitud:', error);
        console.error('Respuesta del error:', error.response);
        let errorMessage = error.response?.data?.error || 'Error al subir el archivo';
        if (error.response?.data?.details) {
          errorMessage += ': ' + JSON.stringify(error.response.data.details);
        }
        this.message = errorMessage;
        this.messageIsError = true;
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          this.$router.push('/login');
        }
      } finally {
        this.isUploading = false;
      }
    },
    downloadTemplate() {
      // Definir las columnas de la plantilla
      const headers = [
        'AN 3', 'Fecha', 'Z', 'Total', 'BONOS', 'EFECTIVO',
        'RECIBO BANCARIO', 'TARJETA DEBITO', 'TRANSFERENCIA BANCARIA', 'VALE'
      ];

      // Datos de ejemplo
      const exampleData = [
        'ABA - Caja Unico', '17/03/2025', '3397', '$ 2.642.110,00', '$ 0,00',
        '$ 971.100,00', '$ 191.810,00', '$ 1.179.200,00', '$ 300.000,00', '$ 0,00'
      ];

      // Crear hoja de trabajo con encabezados y datos
      const ws = XLSX.utils.aoa_to_sheet([
        headers, // Fila 1: Encabezados
        exampleData // Fila 2: Datos de ejemplo
      ]);

      // Crear libro de trabajo y añadir la hoja
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Plantilla Arqueo');

      // Descargar el archivo
      XLSX.writeFile(wb, 'plantilla_arqueo_caja.xlsx');
    }
  },
  mounted() {
    if (!this.token) {
      console.log('No hay token, redirigiendo al login');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.upload-arqueo {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.instructions {
  margin-bottom: 20px;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
}

.instructions p {
  margin: 5px 0;
}

.form-group {
  margin-bottom: 20px;
}

input[type="file"] {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  margin-right: 10px;
}

button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #2c3e50;
}

.spinner {
  margin-top: 10px;
  color: #42b983;
  font-weight: bold;
}

.message {
  margin-top: 15px;
  font-weight: bold;
}

.message.error {
  color: red;
}
</style>