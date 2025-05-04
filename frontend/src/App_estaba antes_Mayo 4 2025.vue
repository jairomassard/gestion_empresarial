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
        <!-- Enlace "Menú" dinámico -->
        <router-link
          v-if="showMenuLink"
          :to="menuLinkDestination"
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

    // Determinar si mostrar el enlace "Menú"
    const showMenuLink = computed(() => {
      // No mostrar en la página de login ni en la raíz si es superadmin sin subpágina
      return route.path !== '/login' && !(store.getters.isSuperAdmin && route.path === '/admin');
    });

    // Calcular el destino del enlace "Menú" según la ruta actual
    const menuLinkDestination = computed(() => {
      if (store.getters.isSuperAdmin) {
        // Para superadmin, si está en una subpágina de /admin, vuelve a /admin
        if (route.path.startsWith('/admin/')) {
          return '/admin';
        }
        return '/'; // Menú principal por defecto
      }

      // Para usuarios no superadmin
      if (
        route.path === '/' ||
        route.path === '/analysis' ||
        route.path === '/inventory' ||
        route.path === '/production' ||
        route.path === '/settings'
      ) {
        return '/'; // Si está en un menú principal o en settings, vuelve al MainMenu
      }

      // Si está en una subpágina, regresar al menú correspondiente
      if (
        route.path.startsWith('/analysis/') ||
        route.path === '/dashboard' ||
        route.path.startsWith('/dashboard/') ||
        route.path.startsWith('/upload/') ||
        route.path === '/upload' ||
        route.path.startsWith('/points-of-sale')
      ) {
        return '/analysis';
      }
      if (route.path.startsWith('/inventory/')) {
        return '/inventory';
      }
      if (route.path.startsWith('/production/')) {
        return '/production';
      }
      if (
        route.path.startsWith('/profiles-clientes') ||
        route.path.startsWith('/users-clientes')
      ) {
        return '/'; // Parametrización ahora va al MainMenu
      }

      return '/'; // Por defecto, al MainMenu
    });

    return {
      store,
      route,
      showMenuLink,
      menuLinkDestination,
      logout,
    };
  },
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