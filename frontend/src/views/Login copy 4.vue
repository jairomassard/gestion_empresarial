<template>
  <div class="login-container">
    <div class="login-card">
      <div class="header">
        <h1 class="system-title">Sistema de Análisis Empresarial</h1>
        <p class="subtitle">Inicio de sesión</p>
      </div>
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="usuario">Usuario</label>
          <div class="input-wrapper">
            <font-awesome-icon icon="user" class="input-icon" />
            <input
              type="text"
              id="usuario"
              v-model="usuario"
              placeholder="Ingresa tu usuario"
              required
              autocomplete="username"
            />
          </div>
        </div>
        <div class="form-group">
          <label for="password">Contraseña</label>
          <div class="input-wrapper">
            <font-awesome-icon icon="lock" class="input-icon" />
            <input
              type="password"
              id="password"
              v-model="password"
              placeholder="Ingresa tu contraseña"
              required
              autocomplete="current-password"
            />
          </div>
        </div>
        <button type="submit" class="login-button" :disabled="loading">
          {{ loading ? 'Iniciando...' : 'Iniciar Sesión' }}
        </button>
        <p v-if="error" class="error-message">{{ error }}</p>
      </form>
      <!-- Mensaje si no hay datos -->
      <!--<div class="footer"> -->
      <!--  <p>¿Problemas para iniciar sesión? <a href="#">Contacta al soporte</a></p>-->
      <!--</div> -->
      
    </div>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { ref } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'; // Añadido para los íconos

export default {
  name: 'Login',
  components: { FontAwesomeIcon }, // Registro del componente
  setup() {
    const store = useStore();
    const router = useRouter();
    const usuario = ref('');
    const password = ref('');
    const error = ref('');
    const loading = ref(false);

    const login = async () => {
      loading.value = true;
      error.value = '';
      console.log('Datos enviados al backend:', { usuario: usuario.value, password: password.value });
      try {
        const response = await axios.post('/login', {
          usuario: usuario.value,
          password: password.value
        });
        console.log('Respuesta del backend:', response.data);
        const { token, idcliente, perfilid, permisos, clienteEstado } = response.data;

        if (idcliente) {
          if (clienteEstado === false) {
            error.value = 'Por favor, póngase al día con su mensualidad para uso de la plataforma.';
            loading.value = false;
            return;
          }
          store.commit('setAuth', { token, idcliente, perfilid, permisos });
          console.log('Permisos seteados en store:', store.state.auth.permisos); // Depuración
          await store.dispatch('fetchCliente');
        } else {
          store.commit('setAuth', { token, idcliente, perfilid, permisos });
          console.log('Permisos seteados en store:', store.state.auth.permisos); // Depuración
        }

        if (store.getters.isSuperAdmin) {
          router.push('/admin');
        } else {
          router.push('/');
        }
      } catch (err) {
        error.value = err.response?.data?.error || 'Error al iniciar sesión';
        console.error('Error en login:', err.response?.data);
      } finally {
        loading.value = false;
      }
    };

    return {
      usuario,
      password,
      error,
      loading,
      login
    };
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #e0e7ff 0%, #d1d9e6 100%);
  padding: 20px;
}

.login-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  padding: 30px;
  animation: fadeIn 0.5s ease-in-out;
  box-sizing: border-box; /* Asegura que el padding no expanda el ancho */
}

.header {
  text-align: center;
  margin-bottom: 25px;
}

.system-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.subtitle {
  font-size: 1rem;
  color: #7f8c8d;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  position: relative;
}

label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: #34495e;
  margin-bottom: 6px;
}

.input-wrapper {
  position: relative;
  width: 100%; /* Asegura que el contenedor no exceda el ancho del padre */
}

.input-icon {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: #95a5a6;
  font-size: 1rem;
}

input {
  width: 100%; /* Ocupa el ancho completo del contenedor padre */
  padding: 12px 12px 12px 36px; /* Espacio para el ícono */
  border: 1px solid #dcdcdc;
  border-radius: 6px;
  font-size: 1rem;
  color: #2c3e50;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  box-sizing: border-box; /* Incluye padding y borde en el ancho total */
}

input:focus {
  border-color: #42b983;
  box-shadow: 0 0 5px rgba(66, 185, 131, 0.3);
  outline: none;
}

input::placeholder {
  color: #bdc3c7;
}

.login-button {
  width: 100%;
  padding: 12px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.login-button:hover {
  background-color: #359f6f;
  transform: translateY(-2px);
}

.login-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  font-size: 0.9rem;
  text-align: center;
  margin-top: 15px;
}

.footer {
  text-align: center;
  margin-top: 20px;
}

.footer p {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin: 0;
}

.footer a {
  color: #42b983;
  text-decoration: none;
  font-weight: 600;
}

.footer a:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 20px;
    max-width: 100%;
  }

  .system-title {
    font-size: 1.5rem;
  }

  .subtitle {
    font-size: 0.9rem;
  }
}
</style>