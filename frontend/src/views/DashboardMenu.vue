<template>
    <div class="dashboard-menu">
      <h1>Menú de Dashboards</h1>
      <ul>
        <li><router-link to="/dashboard/historical-sales">Ventas Históricas</router-link></li>
        <li><router-link to="/dashboard/monthly-performance">Rendimiento Mensual</router-link></li>
        <li><router-link to="/dashboard/daily-sales">Venta Diaria por PDV</router-link></li>
        <li><router-link to="/dashboard/sales-by-time-slot">Ventas por Franja del Día</router-link></li>
        <li><router-link to="/dashboard/sales-by-payment-method">Ventas por Medio de Pago</router-link></li>
        <li><router-link to="/dashboard/sales-by-product">Ventas por Producto</router-link></li>
        <li><router-link to="/dashboard/sales-by-seller">Ventas por Asesor</router-link></li>
        <li><router-link to="/dashboard/accumulated-sales-by-pdv">Venta Acumulada por PDV</router-link></li>
        <!-- Añadir más opciones de dashboard aquí en el futuro -->
      </ul>
    </div>
  </template>
  
  <script>
  export default {
    name: 'DashboardMenu',
  };
  </script>
  
  <style scoped>
  .dashboard-menu {
    text-align: center;
    margin-top: 50px;
  }
  ul {
    list-style-type: none;
    padding: 0;
  }
  li {
    margin: 10px 0;
  }
  a {
    text-decoration: none;
    font-size: 18px;
    color: #2c3e50;
  }
  a:hover {
    color: #42b983;
  }
  </style>