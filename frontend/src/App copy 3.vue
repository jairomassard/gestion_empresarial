<template>
  <div class="app">
    <header v-if="store.getters.isAuthenticated">
      <div v-if="store.state.cliente.logo" class="logo">
        <img :src="store.state.cliente.logo" alt="Logo del Cliente" />
      </div>
      <nav>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/clientes">Clientes</router-link>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/perfiles">Perfiles</router-link>
        <router-link v-if="store.getters.isSuperAdmin" to="/admin/usuarios">Usuarios</router-link>
        <!-- Enlace "Menú" para el entorno del cliente -->
        <router-link
          v-if="!store.getters.isSuperAdmin && $route.path !== '/'"
          to="/"
          class="menu-link"
        >
          Menú
        </router-link>
        <!-- Enlace "Menú" para el entorno del superadministrador -->
        <router-link
          v-if="store.getters.isSuperAdmin && isAdminSubPage"
          to="/admin"
          class="menu-link"
        >
          Menú
        </router-link>
        <button @click="logout">Salir</button>
      </nav>
    </header>
    <router-view />
  </div>
</template>

<script>
import { useStore } from 'vuex';
import { useRouter, useRoute } from 'vue-router';
import { computed } from 'vue';

export default {
  setup() {
    const store = useStore();
    const router = useRouter();
    const route = useRoute();

    const logout = () => {
      store.commit('logout');
      router.push('/login');
    };

    // Computamos si estamos en una subpágina del admin donde debe aparecer el enlace "Menú"
    const isAdminSubPage = computed(() => {
      const adminSubPages = ['/admin/clientes', '/admin/perfiles', '/admin/usuarios'];
      return adminSubPages.includes(route.path);
    });

    return {
      store,
      route,
      isAdminSubPage, // Devolvemos la propiedad computada
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
  justify-content: space-between;
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

.menu-link {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
}

.menu-link:hover {
  color: #42b983;
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