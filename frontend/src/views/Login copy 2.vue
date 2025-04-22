<template>
  <div class="login">
    <h2>Iniciar Sesión</h2>
    <form @submit.prevent="login">
      <div class="form-group">
        <label for="usuario">Usuario:</label>
        <input type="text" id="usuario" v-model="usuario" required />
      </div>
      <div class="form-group">
        <label for="password">Contraseña:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <button type="submit">Iniciar Sesión</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { ref } from 'vue';

export default {
  name: 'Login',
  setup() {
    const store = useStore();
    const router = useRouter();
    const usuario = ref('');
    const password = ref('');
    const error = ref('');

    const login = async () => {
      try {
        const response = await axios.post('/login', {
          usuario: usuario.value,
          password: password.value
        });
        const { token, idcliente, perfilid, permisos, clienteEstado } = response.data;

        // Si el usuario pertenece a un cliente, validar el estado del cliente
        if (idcliente) {
          if (clienteEstado === false) {
            error.value = 'Por favor, póngase al día con su mensualidad para uso de la plataforma.';
            return;
          }
          // Guardar datos de autenticación y cargar información del cliente
          store.commit('setAuth', { token, idcliente, perfilid, permisos });
          await store.dispatch('fetchCliente');
        } else {
          // Si no hay idcliente (superadministrador), solo guardar auth
          store.commit('setAuth', { token, idcliente, perfilid, permisos });
        }

        // Redirigir según el tipo de usuario
        if (store.getters.isSuperAdmin) {
          router.push('/admin');
        } else {
          router.push('/');
        }
      } catch (err) {
        error.value = err.response?.data?.error || 'Error al iniciar sesión';
        console.error('Error en login:', err);
      }
    };

    return {
      usuario,
      password,
      error,
      login
    };
  }
};
</script>

<style scoped>
.login {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #f9f9f9;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.error {
  color: red;
  margin-top: 10px;
}
</style>