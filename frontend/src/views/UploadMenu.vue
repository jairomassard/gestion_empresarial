<template>
  <div class="upload-menu">
    <h1>Cargue de Información</h1>
    <ul>
      
      <li><router-link to="/upload/sales">Cargar Ventas diarias</router-link></li>
      <li><router-link to="/upload/arqueo">Cargar Arqueo</router-link></li>
      <li><router-link to="/points-of-sale">Gestionar Puntos de Venta</router-link></li>
      <li><router-link to="/upload/venta-mensual">Cargar Venta Mensual historica</router-link></li>
      <li><router-link to="/upload/budget">Cargar Presupuesto</router-link></li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'UploadMenu',
};
</script>

<style scoped>
.upload-menu {
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