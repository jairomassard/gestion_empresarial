<template>
  <div class="home-container">
    <h1 class="main-title">Sistema de Análisis Empresarial</h1>
    <!-- Agregamos el nombre del cliente aquí -->
    <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
      {{ store.state.cliente.nombre }}
    </h2>
    <div class="sections-grid">
      <!-- Columna Izquierda: DASHBOARD -->
      <div class="section dashboard-section" v-if="store.getters.hasPermission('dashboard', null, 'ver')">
        <h2 class="section-title">
          <font-awesome-icon icon="chart-line" class="section-icon" /> DASHBOARD
        </h2>
        <div class="cards-container">
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'ventas_historicas', 'ver')"
            to="/dashboard/historical-sales"
            class="card"
          >
            <font-awesome-icon icon="history" class="card-icon" />
            <span>Ventas Históricas</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'rendimiento_mensual', 'ver')"
            to="/dashboard/monthly-performance"
            class="card"
          >
            <font-awesome-icon icon="calendar-alt" class="card-icon" />
            <span>Rendimiento Mensual</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'venta_diaria_pdv', 'ver')"
            to="/dashboard/daily-sales"
            class="card"
          >
            <font-awesome-icon icon="store" class="card-icon" />
            <span>Venta Diaria por PDV</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'ventas_franja_dia', 'ver')"
            to="/dashboard/sales-by-time-slot"
            class="card"
          >
            <font-awesome-icon icon="clock" class="card-icon" />
            <span>Ventas por Franja del Día</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'ventas_medio_pago', 'ver')"
            to="/dashboard/sales-by-payment-method"
            class="card"
          >
            <font-awesome-icon icon="credit-card" class="card-icon" />
            <span>Ventas por Medio de Pago</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'ventas_producto', 'ver')"
            to="/dashboard/sales-by-product"
            class="card"
          >
            <font-awesome-icon icon="box" class="card-icon" />
            <span>Ventas por Producto</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'ventas_asesor', 'ver')"
            to="/dashboard/sales-by-seller"
            class="card"
          >
            <font-awesome-icon icon="user-tie" class="card-icon" />
            <span>Ventas por Asesor</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('dashboard', 'venta_acumulada_pdv', 'ver')"
            to="/dashboard/accumulated-sales-by-pdv"
            class="card"
          >
            <font-awesome-icon icon="chart-bar" class="card-icon" />
            <span>Venta Acumulada por PDV</span>
          </router-link>
        </div>
      </div>

      <!-- Columna Derecha: CARGUE DE INFORMACIÓN y PARAMETRIZACIÓN -->
      <div class="right-column">
        <!-- CARGUE DE INFORMACIÓN -->
        <div class="section upload-section" v-if="store.getters.hasPermission('cargue', null, 'editar')">
          <h2 class="section-title">
            <font-awesome-icon icon="upload" class="section-icon" /> CARGUE DE INFORMACIÓN
          </h2>
          <div class="cards-container">
            <router-link to="/upload/sales" class="card">
              <font-awesome-icon icon="file-upload" class="card-icon" />
              <span>Cargar Ventas Diarias</span>
            </router-link>
            <router-link to="/upload/arqueo" class="card">
              <font-awesome-icon icon="cash-register" class="card-icon" />
              <span>Cargar Arqueo</span>
            </router-link>
            <router-link to="/upload/venta-mensual" class="card">
              <font-awesome-icon icon="file-invoice" class="card-icon" />
              <span>Cargar Venta Mensual Histórica</span>
            </router-link>
            <router-link to="/upload/budget" class="card">
              <font-awesome-icon icon="file-excel" class="card-icon" />
              <span>Cargar Presupuesto de Venta</span>
            </router-link>
          </div>
        </div>

        <!-- PARAMETRIZACIÓN -->
        <div class="section settings-section" v-if="store.getters.hasPermission('parametrizacion', null, 'editar')">
          <h2 class="section-title">
            <font-awesome-icon icon="cogs" class="section-icon" /> PARAMETRIZACIÓN
          </h2>
          <div class="cards-container">
            <router-link to="/points-of-sale" class="card">
              <font-awesome-icon icon="map-marker-alt" class="card-icon" />
              <span>Puntos de Venta</span>
            </router-link>
            <router-link to="/profiles-clientes" class="card">
              <font-awesome-icon icon="user" class="card-icon" />
              <span>Creación de perfiles</span>
            </router-link>
            <router-link to="/users-clientes" class="card">
              <font-awesome-icon icon="users" class="card-icon" />
              <span>Creación de Usuarios</span>
            </router-link>
            
          </div>
        </div>
      </div>
    </div>

    <!-- Logo del Cliente (eliminamos esta sección porque ya está en App.vue) -->
  </div>
</template>

<script>
import { useStore } from 'vuex';

export default {
  name: 'Home',
  setup() {
    const store = useStore();
    return { store };
  }
};
</script>

<style scoped>
.home-container {
  padding: 10px;
  max-width: 1080px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f4f7fa 0%, #d9e2ec 100%);
  height: auto;
}

.main-title {
  text-align: center;
  font-size: 1.8rem;
  /*  margin-bottom: 15px;*/
  margin-bottom: 5px; /* Reducimos el margen inferior para que el nombre del cliente quede cerca */
  color: #2c3e50;
  font-weight: 700;
}


/* Estilo para el nombre del cliente */
.cliente-nombre {
  text-align: center;
  font-size: 1.4rem; /* Un poco más pequeño que el título principal */
  margin-bottom: 15px;
  color: #34495e; /* Un color ligeramente más oscuro para diferenciarlo */
  font-weight: 600;
}

.sections-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.section {
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.section:hover {
  transform: translateY(-3px);
}

.dashboard-section {
  background-color: #ffffff;
  border-left: 4px solid #42b983;
}

.upload-section {
  background-color: #ffffff;
  border-left: 4px solid #3498db;
}

.settings-section {
  background-color: #ffffff;
  border-left: 4px solid #e74c3c;
}

.section-title {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: #34495e;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-icon {
  font-size: 1rem;
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 6px;
  text-decoration: none;
  color: #2c3e50;
  font-weight: 500;
  font-size: 0.85rem;
  text-align: center;
  transition: background-color 0.3s ease, transform 0.2s ease;
  height: 70px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.card:hover {
  background-color: #e0e0e0;
  transform: scale(1.03);
}

.card-icon {
  font-size: 1.2rem;
  margin-bottom: 6px;
  color: #666;
}

@media (max-width: 1024px) {
  .sections-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .cards-container {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}
</style>