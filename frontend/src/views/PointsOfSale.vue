<template>
  <div class="points-of-sale">
    <h1>Gestión de Puntos de Venta</h1>

    <!-- Filtros -->
    <div class="filters">
      <label>Estatus:</label>
      <select v-model="selectedStatus" @change="fetchPointsOfSale">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <button @click="openCreateModal" class="create-btn">Agregar Punto de Venta</button>
    </div>

    <!-- Tabla de Puntos de Venta -->
    <div class="table-container">
      <table class="points-table">
        <thead>
          <tr>
            <th>Código (data1)</th>
            <th>Nombre (data2)</th>
            <th>PDV</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="point in pointsOfSale" :key="point.id">
            <td>{{ point.data1 }}</td>
            <td>{{ point.data2 }}</td>
            <td>{{ point.pdv }}</td>
            <td>{{ point.estado }}</td>
            <td>
              <button @click="openEditModal(point)" class="edit-btn">Editar</button>
              <button @click="deletePointOfSale(point.id)" class="delete-btn">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal para Crear/Editar -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">
        <h2>{{ isEditing ? 'Editar Punto de Venta' : 'Agregar Punto de Venta' }}</h2>
        <form @submit.prevent="savePointOfSale">
          <div class="form-group">
            <label>Código (data1):</label>
            <input v-model="form.data1" type="text" maxlength="50" required />
          </div>
          <div class="form-group">
            <label>Nombre (data2):</label>
            <input v-model="form.data2" type="text" maxlength="50" required />
          </div>
          <div class="form-group">
            <label>PDV:</label>
            <input v-model="form.pdv" type="text" maxlength="200" required />
          </div>
          <div class="form-group">
            <label>Estado:</label>
            <select v-model="form.estado" required>
              <option value="Activo">Activo</option>
              <option value="Inactivo">Inactivo</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="submit" class="save-btn" :disabled="loading">
              {{ isEditing ? 'Guardar Cambios' : 'Crear' }}
            </button>
            <button type="button" @click="closeModal" class="cancel-btn">Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '@/api/axios';
import { mapState } from 'vuex';

export default {
  name: 'PointsOfSale',
  computed: {
    ...mapState({
      token: state => state.auth.token,
      idcliente: state => state.auth.idcliente
    })
  },
  data() {
    return {
      selectedStatus: 'Activo', // Filtro por defecto
      pointsOfSale: [], // Lista de puntos de venta
      showModal: false, // Controla la visibilidad del modal
      isEditing: false, // Determina si estamos editando o creando
      form: {
        id: null,
        data1: '',
        data2: '',
        pdv: '',
        estado: 'Activo', // Valor por defecto
      },
      loading: false // Controla el estado de carga
    };
  },
  methods: {
    async fetchPointsOfSale() {
      try {
        const response = await axios.get('/points-of-sale', {
          params: { status: this.selectedStatus },
          headers: { Authorization: `Bearer ${this.token}` }
        });
        this.pointsOfSale = response.data;
      } catch (error) {
        console.error('Error fetching points of sale:', error);
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          this.$router.push('/login');
        } else {
          alert('Error al cargar los puntos de venta: ' + (error.response?.data?.error || error.message));
        }
      }
    },
    openCreateModal() {
      this.isEditing = false;
      this.form = {
        id: null,
        data1: '',
        data2: '',
        pdv: '',
        estado: 'Activo'
      };
      this.showModal = true;
    },
    openEditModal(point) {
      this.isEditing = true;
      this.form = { ...point };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
    },
    async savePointOfSale() {
      if (!this.validateForm()) return;

      this.loading = true;
      try {
        const data = {
          idcliente: this.idcliente,
          data1: this.form.data1,
          data2: this.form.data2,
          pdv: this.form.pdv,
          estado: this.form.estado
        };
        console.log('Sending data to /points-of-sale:', data); // Depuración

        let response;
        if (this.isEditing) {
          // Actualizar punto de venta
          response = await axios.put(`/points-of-sale/${this.form.id}`, {
            data1: data.data1,
            data2: data.data2,
            pdv: data.pdv,
            estado: data.estado
          }, {
            headers: { Authorization: `Bearer ${this.token}` }
          });
          const updatedPoint = response.data;
          const index = this.pointsOfSale.findIndex(p => p.id === updatedPoint.id);
          if (index !== -1) {
            this.pointsOfSale.splice(index, 1, updatedPoint);
          }
          alert('Punto de venta actualizado exitosamente');
        } else {
          // Crear nuevo punto de venta
          response = await axios.post('/points-of-sale', data, {
            headers: { Authorization: `Bearer ${this.token}` }
          });
          this.pointsOfSale.push(response.data);
          alert('Punto de venta creado exitosamente');
        }
        this.closeModal();
      } catch (error) {
        console.error('Error saving point of sale:', error);
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          this.$router.push('/login');
        } else if (error.response && error.response.status === 409) {
          alert('Error: El nombre del PDV ya existe. Por favor, usa un nombre único.');
        } else {
          alert('Error al guardar el punto de venta: ' + (error.response?.data?.error || error.message));
        }
      } finally {
        this.loading = false;
      }
    },
    validateForm() {
      if (!this.form.data1 || this.form.data1.length > 50) {
        alert('Código (data1) es requerido y debe tener máximo 50 caracteres');
        return false;
      }
      if (!this.form.data2 || this.form.data2.length > 50) {
        alert('Nombre (data2) es requerido y debe tener máximo 50 caracteres');
        return false;
      }
      if (!this.form.pdv || this.form.pdv.length > 200) {
        alert('PDV es requerido y debe tener máximo 200 caracteres');
        return false;
      }
      if (!['Activo', 'Inactivo'].includes(this.form.estado)) {
        alert('Estado debe ser Activo o Inactivo');
        return false;
      }
      if (!this.idcliente) {
        alert('ID del cliente no está disponible. Por favor, inicia sesión nuevamente.');
        return false;
      }
      return true;
    },
    async deletePointOfSale(id) {
      if (confirm('¿Estás seguro de que deseas eliminar este punto de venta?')) {
        try {
          await axios.delete(`/points-of-sale/${id}`, {
            headers: { Authorization: `Bearer ${this.token}` }
          });
          this.pointsOfSale = this.pointsOfSale.filter(p => p.id !== id);
          alert('Punto de venta eliminado exitosamente');
        } catch (error) {
          console.error('Error deleting point of sale:', error);
          if (error.response && error.response.status === 401) {
            console.log('No autorizado, redirigiendo al login');
            this.$router.push('/login');
          } else if (error.response && error.response.status === 409) {
            alert('Error: No se puede eliminar este punto de venta porque está siendo usado en otras tablas.');
          } else {
            alert('Error al eliminar el punto de venta: ' + (error.response?.data?.error || error.message));
          }
        }
      }
    }
  },
  mounted() {
    if (this.token) {
      this.fetchPointsOfSale();
    } else {
      console.log('No hay token, redirigiendo al login');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.points-of-sale {
  padding: 20px;
}

.filters {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
}

label {
  margin-right: 10px;
}

select {
  padding: 5px;
}

.create-btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
}

.create-btn:hover {
  background-color: #2c3e50;
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
  display: flex; /* Usamos flex para centrar la tabla */
  justify-content: center; /* Centramos horizontalmente */
  margin-bottom: 20px;
}

.points-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.points-table th,
.points-table td {
  border: 1px solid #ddd;
  padding: 6px;
  text-align: center;
}

.points-table th {
  background-color: #f2f2f2;
  font-size: 12px;
}

.points-table td {
  max-width: 150px;
  white-space: nowrap;
}

.edit-btn,
.delete-btn {
  padding: 4px 8px;
  margin: 0 5px;
  border: none;
  cursor: pointer;
  font-size: 12px;
}

.edit-btn {
  background-color: #42b983;
  color: white;
}

.edit-btn:hover {
  background-color: #2c3e50;
}

.delete-btn {
  background-color: #ff4444;
  color: white;
}

.delete-btn:hover {
  background-color: #cc0000;
}

/* Estilos del Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.save-btn,
.cancel-btn {
  padding: 8px 16px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.save-btn {
  background-color: #42b983;
  color: white;
}

.save-btn:hover {
  background-color: #2c3e50;
}

.cancel-btn {
  background-color: #ff4444;
  color: white;
}

.cancel-btn:hover {
  background-color: #cc0000;
}
</style>