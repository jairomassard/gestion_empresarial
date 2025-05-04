<template>
  <div class="inventory-menu-container">
    <h1 class="main-title">Módulo de Inventario</h1>
    <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
      {{ store.state.cliente.nombre }}
    </h2>
    <div class="sections-grid">
      <!-- INVENTARIO -->
      <div class="section inventory-section" v-if="store.getters.hasPermission('inventario', null, 'ver')">
        <h2 class="section-title">
          <font-awesome-icon icon="warehouse" class="section-icon" /> INVENTARIO
        </h2>
        <div class="cards-container">
          <router-link
            v-if="store.getters.hasPermission('inventario', 'consulta_inventario', 'ver')"
            to="/inventory/consulta-inventario"
            class="card"
          >
            <font-awesome-icon icon="search" class="card-icon" />
            <span>Consulta de Inventario</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'consulta', 'ver')"
            to="/inventory/consulta-lite"
            class="card"
          >
            <font-awesome-icon icon="search" class="card-icon" />
            <span>Consulta de Inventario (Solo Cantidades)</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'kardex', 'ver')"
            to="/inventory/kardex"
            class="card"
          >
            <font-awesome-icon icon="clipboard-list" class="card-icon" />
            <span>Kardex de Inventario</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'gestion_productos', 'editar')"
            to="/inventory/gestion-productos-materiales"
            class="card"
          >
            <font-awesome-icon icon="list" class="card-icon" />
            <span>Gestión de Productos y Materiales</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'bodegas', 'editar')"
            to="/inventory/bodegas"
            class="card"
          >
            <font-awesome-icon icon="boxes" class="card-icon" />
            <span>Gestión de Almacenes</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'traslados', 'ver')"
            to="/inventory/trasladar-cantidades"
            class="card"
          >
            <font-awesome-icon icon="exchange-alt" class="card-icon" />
            <span>Trasladar Cantidades entre Almacenes</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'ajustes', 'ver')"
            to="/inventory/ajuste-inventario"
            class="card"
          >
            <font-awesome-icon icon="cogs" class="card-icon" />
            <span>Ajuste Manual de Inventario</span>
          </router-link>
        </div>
      </div>

      <!-- CARGUE DE INFORMACIÓN -->
      <div class="section upload-section" v-if="store.getters.hasPermission('cargue', null, 'editar')">
        <h2 class="section-title">
          <font-awesome-icon icon="upload" class="section-icon" /> CARGUE DE INFORMACIÓN PARA INVENTARIO
        </h2>
        <div class="cards-container">
          <router-link
            v-if="store.getters.hasPermission('inventario', 'compras', 'editar')"
            to="/inventory/cargar-compras"
            class="card"
          >
            <font-awesome-icon icon="cart-plus" class="card-icon" />
            <span>Cargar Compras de Producto</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'ventas', 'editar')"
            to="/inventory/ventas"
            class="card"
          >
            <font-awesome-icon icon="cash-register" class="card-icon" />
            <span>Cargar Ventas Manualmente</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('inventario', 'notas_credito', 'editar')"
            to="/inventory/notas-credito"
            class="card"
          >
            <font-awesome-icon icon="undo" class="card-icon" />
            <span>Cargar Notas Crédito</span>
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
  name: 'InventoryMenu',
  components: { FontAwesomeIcon },
  setup() {
    const store = useStore();
    return { store };
  },
};
</script>

<style scoped>
.inventory-menu-container {
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