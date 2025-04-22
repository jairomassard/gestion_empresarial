<template>
    <div>
      <h2>Cargar Arqueo de Caja</h2>
      <input type="file" @change="handleFileUpload" accept=".xlsx" />
      <button @click="uploadFile" :disabled="!file">Subir</button>
      <p>{{ message }}</p>
    </div>
  </template>
  
  <script>
  import axios from '@/api/axios';
  import { mapState } from 'vuex';
  
  export default {

    data() {
      return {
        file: null,
        message: ''
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
      },
      async uploadFile() {
        const formData = new FormData();
        formData.append('file', this.file);

        try {
          const response = await axios.post('/upload_arqueo', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          this.message = response.data.message;
        } catch (error) {
          this.message = error.response?.data?.error || 'Error al subir';
          if (error.response?.data?.details) {
            this.message += ': ' + JSON.stringify(error.response.data.details);
          }
          if (error.response && error.response.status === 401) {
            console.log('No autorizado, redirigiendo al login');
            this.$router.push('/login');
          }
        }
      },
    },
    mounted() {
      if (!this.token) {
        console.log('No hay token, redirigiendo al login');
        this.$router.push('/login');
      }
    },

  };
  </script>