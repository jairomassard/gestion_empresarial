<template>
  <div class="app">
    <header v-if="store.getters.isAuthenticated">
      <div v-if="store.state.cliente.logo" class="logo">
        <img :src="store.state.cliente.logo" alt="Logo del Cliente" />
      </div>
      <!--<h1>{{ store.state.cliente.nombre || 'Sistema de Análisis Empresarial' }}</h1>-->
      <nav>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/clientes">Clientes</router-link>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/perfiles">Perfiles</router-link>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/usuarios">Usuarios</router-link>
        <!-- Agregamos el enlace "Menú" condicionalmente -->
        <router-link v-if="$route.path !== '/'" to="/" class="menu-link">Menú</router-link>
        <button @click="logout">Salir</button>
      </nav>
    </header>
    <router-view />
  </div>
</template>

<script>
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const store = useStore();
    const router = useRouter();
    const route = useRoute(); // Agregamos useRoute para acceder a la ruta actual

    const logout = () => {
      store.commit('logout');
      router.push('/login');
    };

    return {
      store,
      route, // Devolvemos route para usarlo en el template
      logout
    };
  }
};
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

header {
  display: flex;
  justify-content: space-between; /* Logo a la izquierda, navegación a la derecha */
  align-items: center;
  padding: 10px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.logo img {
  max-height: 50px;
}

nav {
  display: flex;
  gap: 15px;
  align-items: center;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
}

nav a.router-link-exact-active {
  color: #42b983;
}

/* Estilo específico para el enlace "Menú" */
.menu-link {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
}

.menu-link:hover {
  color: #42b983; /* Color verde al pasar el ratón, igual que los otros enlaces activos */
}

nav button {
  padding: 5px 10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

nav button:hover {
  background-color: #c0392b;
}
</style>