<template>
  <div class="main-menu-container">
    <h1 class="main-title">Sistema de Gestión Empresarial</h1>
    <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
      {{ store.state.cliente.nombre }}
    </h2>
    <div class="modules-grid">
      <router-link to="/analysis" class="module-card">
        <font-awesome-icon icon="chart-line" class="module-icon" />
        <span>Análisis</span>
      </router-link>
      <router-link to="/inventory" class="module-card">
        <font-awesome-icon icon="warehouse" class="module-icon" />
        <span>Inventario</span>
      </router-link>
      <router-link to="/production" class="module-card">
        <font-awesome-icon icon="industry" class="module-icon" />
        <span>Producción</span>
      </router-link>
      <router-link
        v-if="store.getters.hasPermission('parametrizacion', null, 'editar')"
        to="/settings"
        class="module-card"
      >
        <font-awesome-icon icon="cogs" class="module-icon" />
        <span>Parametrización</span>
      </router-link>

    </div>
  </div>
</template>

<script>
import { useStore } from 'vuex';

export default {
  name: 'MainMenu',
  setup() {
    const store = useStore();
    return { store };
  }
};
</script>

<style scoped>
.main-menu-container {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 20px;
}

.cliente-nombre {
  font-size: 1.5rem;
  color: #34495e;
  margin-bottom: 40px;
}

.modules-grid {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.module-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 200px;
  height: 200px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  color: #34495e;
  font-weight: 600;
  font-size: 1.2rem;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.module-card:hover {
  transform: translateY(-5px);
  background-color: #e0e7ff;
}

.module-icon {
  font-size: 2.5rem;
  color: #42b983;
  margin-bottom: 15px;
}

@media (max-width: 768px) {
  .modules-grid {
    flex-direction: column;
    align-items: center;
  }
}
</style>