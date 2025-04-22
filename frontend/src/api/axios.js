import axios from 'axios';
import store from '@/store'; // Ajusta la ruta según la ubicación de tu store (puede ser '@/store/index' o similar)

// Configurar la URL base usando la variable de entorno
const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:5000';

// Crear una instancia de axios con la URL base
const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000, // Opcional: tiempo máximo de espera para las solicitudes (en milisegundos)
  // No establecer Content-Type por defecto
  //headers: {
  //  'Content-Type': 'application/json',
  //},
});

// Interceptor de solicitud para agregar el token de autorización
axiosInstance.interceptors.request.use(
  (config) => {
    const token = store.state.auth.token; // Ajusta según la estructura de tu store
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de respuesta para manejar errores globalmente
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Error en la solicitud:', error);
    if (error.response?.status === 401) {
      store.commit('logout');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;