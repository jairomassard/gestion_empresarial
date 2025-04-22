<template>
  <div class="home-container">
    <h1 class="main-title">Sistema de Análisis Empresarial</h1>
    <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
      {{ store.state.cliente.nombre }}
    </h2>
    <div class="sections-grid">
      <!-- DASHBOARD -->
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

      <!-- CARGUE DE INFORMACIÓN -->
      <div class="section upload-section" v-if="store.getters.hasPermission('cargue', null, 'editar')">
        <h2 class="section-title">
          <font-awesome-icon icon="upload" class="section-icon" /> CARGUE DE INFORMACIÓN
        </h2>
        <div class="cards-container">
          <router-link
            v-if="store.getters.hasPermission('cargue', 'ventas_diarias', 'editar')"
            to="/upload/sales"
            class="card"
          >
            <font-awesome-icon icon="file-upload" class="card-icon" />
            <span>Cargar Ventas Diarias</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('cargue', 'arqueo', 'editar')"
            to="/upload/arqueo"
            class="card"
          >
            <font-awesome-icon icon="cash-register" class="card-icon" />
            <span>Cargar Arqueo</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('cargue', 'venta_mensual_historica', 'editar')"
            to="/upload/venta-mensual"
            class="card"
          >
            <font-awesome-icon icon="file-invoice" class="card-icon" />
            <span>Cargar Venta Mensual Histórica</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('cargue', 'presupuesto_venta', 'editar')"
            to="/upload/budget"
            class="card"
          >
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
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'puntos_de_venta', 'editar')"
            to="/points-of-sale"
            class="card"
          >
            <font-awesome-icon icon="map-marker-alt" class="card-icon" />
            <span>Puntos de Venta</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'perfiles', 'editar')"
            to="/profiles-clientes"
            class="card"
          >
            <font-awesome-icon icon="user" class="card-icon" />
            <span>Creación de Perfiles</span>
          </router-link>
          <router-link
            v-if="store.getters.hasPermission('parametrizacion', 'usuarios', 'editar')"
            to="/users-clientes"
            class="card"
          >
            <font-awesome-icon icon="users" class="card-icon" />
            <span>Creación de Usuarios</span>
          </router-link>
        </div>
      </div>
    </div>
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