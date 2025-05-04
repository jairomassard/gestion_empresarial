<template>
  <div class="settings-menu-container">
    <h1 class="main-title">Módulo de Parametrización</h1>
    <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
      {{ store.state.cliente.nombre }}
    </h2>
    <div class="sections-grid">
      <!-- PARAMETRIZACIÓN -->
      <div class="section settings-section" v-if="store.getters.hasPermission('parametrizacion', null, 'editar')">
        <h2 class="section-title">
          <font-awesome-icon icon="cogs" class="section-icon" /> PARAMETRIZACIÓN
        </h2>
        <div class="cards-container">
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'perfiles', 'editar')"
            to="/profiles-clientes"
            class="card"
          >
            <font-awesome-icon icon="user" class="card-icon" />
            <span>Creación y Edición de Perfiles</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'usuarios', 'editar')"
            to="/users-clientes"
            class="card"
          >
            <font-awesome-icon icon="users" class="card-icon" />
            <span>Creación y Edición de Usuarios</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'cutoff', 'editar')"
            to="/cutoff-config"
            class="card"
          >
            <font-awesome-icon icon="calendar-alt" class="card-icon" />
            <span>Configuración Mes de Corte Históricos</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'sync_config', 'editar')"
            to="/sync-config"
            class="card"
          >
            <font-awesome-icon icon="sync" class="card-icon" />
            <span>Configuración de Sincronización Módulos</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useStore } from 'vuex';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  name: 'SettingsMenu',
  components: { FontAwesomeIcon },
  setup() {
    const store = useStore();
    return { store };
  },
};
</script>

<style scoped>
.settings-menu-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  text-align: center;
  margin-bottom: 20px;
}

.cliente-nombre {
  font-size: 1.5rem;
  color: #34495e;
  text-align: center;
  margin-bottom: 30px;
}

.sections-grid {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.section {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
  transition: transform 0.2s ease;
}

.section:hover {
  transform: translateY(-5px);
}

.section-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  font-size: 1.2rem;
  color: #42b983;
}

.cards-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
}

.card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  text-decoration: none;
  color: #34495e;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.card:hover {
  background-color: #e0e7ff;
}

.card-icon {
  font-size: 1.1rem;
  color: #42b983;
}

@media (max-width: 768px) {
  .sections-grid {
    flex-direction: column;
    align-items: center;
  }

  .section {
    max-width: 100%;
  }
}
</style>
