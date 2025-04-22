<template>
    <div class="admin">
      <h2>Panel de Superadministrador</h2>
      <router-view />
    </div>
  </template>
  
  <script>
  export default {
    name: 'Admin'
  };
  </script>
  
  <style scoped>
  .admin {
    padding: 20px;
  }
  </style>