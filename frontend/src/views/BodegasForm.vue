<template>
    <div class="gestion-bodegas">
      <h1>Gestión de Almacenes</h1>
  
      <!--<div class="top-buttons"> -->
      <!--  <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú</button> -->
      <!--</div> -->
  
      <!-- Formulario para Crear/Editar Bodega -->
      <section class="form-section">
        <h2>{{ modoEdicion ? 'Editar Almacén' : 'Crear Almacén' }}</h2>
        <form @submit.prevent="modoEdicion ? actualizarBodega() : crearBodega()">
          <div class="form-group">
            <label for="nombre">Nombre del Almacén:</label>
            <input v-model="bodega.nombre" id="nombre" required />
          </div>
          <div class="form-actions">
            <button v-if="!modoEdicion" type="submit">Crear Almacén</button>
            <template v-else>
              <button type="submit">Guardar Almacén</button>
              <button type="button" @click="cancelarEdicion">Cancelar</button>
            </template>
          </div>
        </form>
      </section>
  
      <!-- Lista de Bodegas -->
      <section class="consulta-bodegas">
        <h2>Almacenes Creados</h2>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bod in bodegas" :key="bod.id">
                <td>{{ bod.id }}</td>
                <td>{{ bod.nombre }}</td>
                <td>
                  <button @click="editarBodega(bod)">Editar</button>
                  <button @click="eliminarBodega(bod.id)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </template>

<script>
import { ref } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import axios from '@/api/axios';

export default {
  name: 'BodegasForm',
  setup() {
    const store = useStore();
    const router = useRouter();

    const bodega = ref({ id: null, nombre: '' });
    const bodegas = ref([]);
    const modoEdicion = ref(false);

    const crearBodega = async () => {
      try {
        await axios.post('/inventory/bodegas', bodega.value);
        alert('Almacén creado correctamente');
        cargarBodegas();
        resetearFormulario();
      } catch (error) {
        console.error('Error al crear almacén:', error);
        alert(error.response?.data?.error || 'Error al crear almacén');
      }
    };

    const cargarBodegas = async () => {
      try {
        const response = await axios.get('/inventory/bodegas');
        bodegas.value = response.data.sort((a, b) => a.nombre.localeCompare(b.nombre));
      } catch (error) {
        console.error('Error al cargar almacenes:', error);
        if (error.response?.status === 403) {
          alert('No tienes permiso para ver los almacenes.');
        } else {
          alert('Ocurrió un error al cargar los almacenes.');
        }
      }
    };

    const editarBodega = (bod) => {
      modoEdicion.value = true;
      bodega.value = { ...bod };
    };

    const actualizarBodega = async () => {
      try {
        await axios.put(`/inventory/bodegas/${bodega.value.id}`, bodega.value);
        alert('Almacén actualizado correctamente');
        cargarBodegas();
        cancelarEdicion();
      } catch (error) {
        console.error('Error al actualizar almacén:', error);
        alert(error.response?.data?.error || 'Error al actualizar almacén');
      }
    };

    const eliminarBodega = async (id) => {
      if (confirm('¿Estás seguro de que deseas eliminar este almacén?')) {
        try {
          await axios.delete(`/inventory/bodegas/${id}`);
          alert('Almacén eliminado correctamente');
          cargarBodegas();
        } catch (error) {
          console.error('Error al eliminar almacén:', error);
          alert(error.response?.data?.error || 'Error al eliminar almacén');
        }
      }
    };

    const cancelarEdicion = () => {
      modoEdicion.value = false;
      resetearFormulario();
    };

    const resetearFormulario = () => {
      bodega.value = { id: null, nombre: '' };
    };

    const volverAlMenu = () => {
      router.push('/inventory');
    };

    // Cargar bodegas al montar el componente
    cargarBodegas();

    return {
      bodega,
      bodegas,
      modoEdicion,
      crearBodega,
      cargarBodegas,
      editarBodega,
      actualizarBodega,
      eliminarBodega,
      cancelarEdicion,
      resetearFormulario,
      volverAlMenu
    };
  }
};
</script>

<style scoped>
.gestion-bodegas {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  font-size: 2rem;
  color: #2c3e50;
  text-align: center;
  margin-bottom: 20px;
}

h2 {
  font-size: 1.5rem;
  color: #34495e;
  margin-bottom: 15px;
}

.top-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  justify-content: flex-end;
}

button, .btn {
  padding: 8px 16px;
  background-color: #42b983; /* Verde característico */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

button:hover, .btn:hover {
  background-color: #2c3e50; /* Hover oscuro */
}

.btn-secondary {
  background-color: #6c757d; /* Gris para volver */
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.form-section, .consulta-bodegas {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
  display: flex;
  justify-content: center;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: center;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
  color: #34495e;
}

td {
  max-width: 200px;
  white-space: normal;
  word-wrap: break-word;
}

td:first-child {
  text-align: left;
}

tbody tr:nth-child(odd) {
  background-color: #f9f9f9;
}

tbody tr:hover {
  background-color: #f1f1f1;
}
</style>
