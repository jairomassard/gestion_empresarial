import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import Vue3Toastify from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

// Agregar los íconos a la librería
library.add(fas);

// Crear la aplicación
const app = createApp(App);

// Registrar Font Awesome como componente global
app.component('font-awesome-icon', FontAwesomeIcon);

// Usar el router, el store y Vue3Toastify
app.use(router);
app.use(store);
app.use(Vue3Toastify, {
  autoClose: 3000,
  position: 'top-right',
  transition: 'slide'
});

// Montar la aplicación
app.mount('#app');
