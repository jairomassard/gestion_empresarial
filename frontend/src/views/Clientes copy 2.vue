<template>
    <div class="clientes">
      <h3>Gestión de Clientes</h3>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <form @submit.prevent="isEditing ? updateCliente() : createCliente()">
        <div class="form-group">
          <label for="nombre">Nombre:</label>
          <input type="text" id="nombre" v-model="nombre" required />
        </div>
        <div class="form-group">
          <label for="nit_cc">NIT/CC:</label>
          <input type="text" id="nit_cc" v-model="nit_cc" required />
        </div>
        <div class="form-group">
          <label for="pais">País:</label>
          <input type="text" id="pais" v-model="pais" required />
        </div>
        <div class="form-group">
          <label for="ciudad">Ciudad:</label>
          <input type="text" id="ciudad" v-model="ciudad" required />
        </div>
        <div class="form-group">
          <label for="direccion_ppal">Dirección Principal:</label>
          <input type="text" id="direccion_ppal" v-model="direccion_ppal" required />
        </div>
        <div class="form-group">
          <label for="tel1">Teléfono 1:</label>
          <input type="text" id="tel1" v-model="tel1" required />
        </div>
        <div class="form-group">
          <label for="correo">Correo:</label>
          <input type="email" id="correo" v-model="correo" required />
        </div>
        <div class="form-group">
          <label for="logo">Logo (URL):</label>
          <input type="text" id="logo" v-model="logo" placeholder="Ej: /logos/cliente.png" />
        </div>
        <button v-if="!isEditing" type="submit">Crear Cliente</button>
        <div v-else>
          <button type="submit">Guardar</button>
          <button type="button" @click="cancelEdit">Cancelar</button>
        </div>
      </form>
      <h3>Clientes Existentes</h3>
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>NIT/CC</th>
            <th>País</th>
            <th>Ciudad</th>
            <th>Dirección</th>
            <th>Teléfono 1</th>
            <th>Correo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cliente in clientes" :key="cliente.idcliente">
            <td>{{ cliente.nombre }}</td>
            <td>{{ cliente.nit_cc }}</td>
            <td>{{ cliente.pais }}</td>
            <td>{{ cliente.ciudad }}</td>
            <td>{{ cliente.direccion_ppal }}</td>
            <td>{{ cliente.tel1 }}</td>
            <td>{{ cliente.correo }}</td>
            <td>
              <button @click="editCliente(cliente)">Editar</button>
              <button @click="deleteCliente(cliente.idcliente)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import axios from '@/api/axios';
  import { ref, onMounted } from 'vue';
  import { useStore } from 'vuex';
  
  export default {
    name: 'Clientes',
    setup() {
      const store = useStore();
      const clientes = ref([]);
      const nombre = ref('');
      const nit_cc = ref('');
      const pais = ref('');
      const ciudad = ref('');
      const direccion_ppal = ref('');
      const tel1 = ref('');
      const correo = ref('');
      const logo = ref('');
      const errorMessage = ref('');
      const isEditing = ref(false); // Estado para saber si estamos editando
      const editingClienteId = ref(null); // ID del cliente que se está editando
  
      const fetchClientes = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) {
            errorMessage.value = 'No se encontró un token de autenticación. Por favor, inicia sesión nuevamente.';
            return;
          }
          console.log('Token enviado:', token);
          const response = await axios.get('/clientes', {
            headers: { Authorization: `Bearer ${token}` },
          });
          console.log('Clientes obtenidos:', response.data);
          clientes.value = response.data;
          errorMessage.value = '';
        } catch (err) {
          console.error('Error al obtener clientes:', err);
          if (err.response) {
            errorMessage.value = err.response.data.msg || 'Error al obtener los clientes. Por favor, intenta de nuevo.';
          } else {
            errorMessage.value = 'Error de conexión con el servidor. Por favor, verifica tu conexión e intenta de nuevo.';
          }
        }
      };
  
      const createCliente = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) {
            errorMessage.value = 'No se encontró un token de autenticación. Por favor, inicia sesión nuevamente.';
            return;
          }
          await axios.post(
            '/clientes',
            {
              nombre: nombre.value,
              nit_cc: nit_cc.value,
              pais: pais.value,
              ciudad: ciudad.value,
              direccion_ppal: direccion_ppal.value,
              tel1: tel1.value,
              correo: correo.value,
              logo: logo.value || null,
            },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          fetchClientes();
        } catch (err) {
          console.error('Error al crear cliente:', err);
          if (err.response) {
            errorMessage.value = err.response.data.msg || 'Error al crear el cliente. Por favor, verifica los datos e intenta de nuevo.';
          } else {
            errorMessage.value = 'Error de conexión con el servidor. Por favor, verifica tu conexión e intenta de nuevo.';
          }
        }
      };
  
      const editCliente = (cliente) => {
        isEditing.value = true;
        editingClienteId.value = cliente.idcliente;
        nombre.value = cliente.nombre;
        nit_cc.value = cliente.nit_cc;
        pais.value = cliente.pais;
        ciudad.value = cliente.ciudad;
        direccion_ppal.value = cliente.direccion_ppal;
        tel1.value = cliente.tel1;
        correo.value = cliente.correo;
        logo.value = cliente.logo || '';
      };
  
      const updateCliente = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) {
            errorMessage.value = 'No se encontró un token de autenticación. Por favor, inicia sesión nuevamente.';
            return;
          }
          await axios.put(
            `/clientes/${editingClienteId.value}`,
            {
              nombre: nombre.value,
              nit_cc: nit_cc.value,
              pais: pais.value,
              ciudad: ciudad.value,
              direccion_ppal: direccion_ppal.value,
              tel1: tel1.value,
              correo: correo.value,
              logo: logo.value || null,
            },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          isEditing.value = false;
          editingClienteId.value = null;
          fetchClientes();
        } catch (err) {
          console.error('Error al actualizar cliente:', err);
          if (err.response) {
            errorMessage.value = err.response.data.msg || 'Error al actualizar el cliente. Por favor, verifica los datos e intenta de nuevo.';
          } else {
            errorMessage.value = 'Error de conexión con el servidor. Por favor, verifica tu conexión e intenta de nuevo.';
          }
        }
      };
  
      const deleteCliente = async (idcliente) => {
        if (confirm('¿Está seguro de eliminar este cliente?')) {
          try {
            const token = store.state.auth.token;
            if (!token) {
              errorMessage.value = 'No se encontró un token de autenticación. Por favor, inicia sesión nuevamente.';
              return;
            }
            await axios.delete(`/clientes/${idcliente}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            fetchClientes();
            errorMessage.value = '';
          } catch (err) {
            console.error('Error al eliminar cliente:', err);
            if (err.response) {
              errorMessage.value = err.response.data.msg || 'Error al eliminar el cliente. Por favor, intenta de nuevo.';
            } else {
              errorMessage.value = 'Error de conexión con el servidor. Por favor, verifica tu conexión e intenta de nuevo.';
            }
          }
        }
      };
  
      const cancelEdit = () => {
        clearForm();
        isEditing.value = false;
        editingClienteId.value = null;
      };
  
      const clearForm = () => {
        nombre.value = '';
        nit_cc.value = '';
        pais.value = '';
        ciudad.value = '';
        direccion_ppal.value = '';
        tel1.value = '';
        correo.value = '';
        logo.value = '';
        errorMessage.value = '';
      };
  
      onMounted(() => {
        fetchClientes();
      });
  
      return {
        clientes,
        nombre,
        nit_cc,
        pais,
        ciudad,
        direccion_ppal,
        tel1,
        correo,
        logo,
        errorMessage,
        isEditing,
        createCliente,
        updateCliente,
        editCliente,
        deleteCliente,
        cancelEdit,
      };
    },
  };
  </script>
  
  <style scoped>
  .clientes {
    padding: 20px;
  }
  
  .form-group {
    margin-bottom: 15px;
  }
  
  label {
    display: block;
    margin-bottom: 5px;
  }
  
  input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  button {
    padding: 10px 20px;
    margin-right: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:hover {
    background-color: #0056b3;
  }
  
  button[type="button"] {
    background-color: #6c757d;
  }
  
  button[type="button"]:hover {
    background-color: #5a6268;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
  }
  
  th,
  td {
    padding: 10px;
    border: 1px solid #ccc;
    text-align: left;
  }
  
  th {
    background-color: #f8f9fa;
  }
  
  .error-message {
    color: red;
    margin-bottom: 15px;
  }
  </style>