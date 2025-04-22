<template>
    <div>
      <h2>Cargar Ventas</h2>
      <input type="file" @change="handleFileUpload" accept=".xlsx" />
      <button @click="uploadFile" :disabled="!file">Subir</button>
      <p>{{ message }}</p>
    </div>
  </template>
  
  <script>
  import axios from '@/api/axios';
  
  export default {
    data() {
      return {
        file: null,
        message: ''
      };
    },
    methods: {
      handleFileUpload(event) {
        this.file = event.target.files[0];
      },
      async uploadFile() {
        const formData = new FormData();
        formData.append('file', this.file);
  
        try {
          const response = await axios.post('/upload_sales', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          this.message = response.data.message;
        } catch (error) {
          this.message = error.response?.data?.error || 'Error al subir';
        }
      }
    }
  };
  </script>