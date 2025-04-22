<template>
    <div class="users">
      <h3>Gestión de Usuarios</h3>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <form @submit.prevent="isEditing ? updateUser() : createUser()">
        <div class="form-group">
          <label for="idcliente">Cliente:</label>
          <select id="idcliente" v-model="idcliente" required>
            <option value="">Seleccione un cliente</option>
            <option v-for="cliente in clientes" :key="cliente.idcliente" :value="cliente.idcliente">
              {{ cliente.nombre }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="perfilid">Perfil:</label>
          <select id="perfilid" v-model="perfilid" required>
            <option value="">Seleccione un perfil</option>
            <option v-for="perfil in perfilesFiltrados" :key="perfil.perfil_id" :value="perfil.perfil_id">
              {{ perfil.perfil_nombre }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="nombres">Nombres:</label>
          <input type="text" id="nombres" v-model="nombres" required />
        </div>
        <div class="form-group">
          <label for="apellidos">Apellidos:</label>
          <input type="text" id="apellidos" v-model="apellidos" required />
        </div>
        <div class="form-group">
          <label for="usuario">Usuario:</label>
          <input type="text" id="usuario" v-model="usuario" required />
        </div>
        <div class="form-group">
          <label for="password">Contraseña:</label>
          <input type="password" id="password" v-model="password" :required="!isEditing" />
        </div>
        <button v-if="!isEditing" type="submit">Crear Usuario</button>
        <div v-else class="edit-buttons">
          <button type="submit">Guardar</button>
          <button type="button" @click="cancelEdit">Cancelar</button>
        </div>
      </form>
      <h3>Usuarios Existentes</h3>
      <table>
        <thead>
          <tr>
            <th>Cliente</th>
            <th>Perfil</th>
            <th>Nombres</th>
            <th>Apellidos</th>
            <th>Usuario</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="usuario in usuarios" :key="usuario.id">
            <td>{{ getClienteNombre(usuario.idcliente) }}</td>
            <td>{{ getPerfilNombre(usuario.perfilid) }}</td>
            <td>{{ usuario.nombres || 'N/A' }}</td>
            <td>{{ usuario.apellidos || 'N/A' }}</td>
            <td>{{ usuario.usuario }}</td>
            <td>{{ usuario.estado ? 'Activo' : 'Inactivo' }}</td>
            <td>
              <button @click="editUser(usuario)">Editar</button>
              <button v-if="usuario.estado" @click="toggleEstado(usuario.id, false)">Desactivar</button>
              <button v-else @click="toggleEstado(usuario.id, true)">Activar</button>
              <button @click="deleteUser(usuario.id)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import axios from '@/api/axios';
  import { ref, onMounted, computed } from 'vue';
  import { useStore } from 'vuex';
  
  export default {
    name: 'Users',
    setup() {
      const store = useStore();
      const clientes = ref([]);
      const perfiles = ref([]);
      const usuarios = ref([]);
      const idcliente = ref('');
      const perfilid = ref('');
      const nombres = ref('');
      const apellidos = ref('');
      const usuario = ref('');
      const password = ref('');
      const errorMessage = ref('');
      const isEditing = ref(false);
      const editingUserId = ref(null);
  
      const perfilesFiltrados = computed(() => {
        return perfiles.value.filter(perfil => perfil.idcliente === idcliente.value || !perfil.idcliente);
      });
  
      const fetchClientes = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const response = await axios.get('/clientes', { headers: { Authorization: `Bearer ${token}` } });
          clientes.value = response.data;
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener clientes';
          console.error('Error al obtener clientes:', err);
        }
      };
  
      const fetchPerfiles = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const response = await axios.get('/perfiles', { headers: { Authorization: `Bearer ${token}` } });
          perfiles.value = response.data;
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener perfiles';
          console.error('Error al obtener perfiles:', err);
        }
      };
  
      const fetchUsuarios = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const response = await axios.get('/usuarios', { headers: { Authorization: `Bearer ${token}` } });
          usuarios.value = response.data;
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener usuarios';
          console.error('Error al obtener usuarios:', err);
        }
      };
  
      const createUser = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          await axios.post(
            '/usuarios',
            {
              idcliente: idcliente.value,
              perfilid: perfilid.value,
              nombres: nombres.value,
              apellidos: apellidos.value,
              usuario: usuario.value,
              password: password.value
            },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          fetchUsuarios();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al crear usuario';
          console.error('Error al crear usuario:', err);
        }
      };
  
      const editUser = (user) => {
        isEditing.value = true;
        editingUserId.value = user.id;
        idcliente.value = user.idcliente;
        perfilid.value = user.perfilid;
        nombres.value = user.nombres;
        apellidos.value = user.apellidos;
        usuario.value = user.usuario;
        password.value = ''; // No cargamos la contraseña por seguridad
      };
  
      const updateUser = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const payload = {
            idcliente: idcliente.value,
            perfilid: perfilid.value,
            nombres: nombres.value,
            apellidos: apellidos.value,
            usuario: usuario.value
          };
          if (password.value) payload.password = password.value; // Solo incluir si se cambió
          await axios.put(
            `/usuarios/${editingUserId.value}`,
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          isEditing.value = false;
          editingUserId.value = null;
          fetchUsuarios();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al actualizar usuario';
          console.error('Error al actualizar usuario:', err);
        }
      };
  
      const toggleEstado = async (id, estado) => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          await axios.patch(
            `/usuarios/${id}/estado`,
            { estado },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          fetchUsuarios();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al actualizar estado';
          console.error('Error al actualizar estado del usuario:', err);
        }
      };
  
      const deleteUser = async (id) => {
        if (confirm('¿Está seguro de eliminar este usuario?')) {
          try {
            const token = store.state.auth.token;
            if (!token) throw new Error('No se encontró token de autenticación');
            await axios.delete(`/usuarios/${id}`, { headers: { Authorization: `Bearer ${token}` } });
            fetchUsuarios();
          } catch (err) {
            errorMessage.value = err.response?.data?.error || 'Error al eliminar usuario';
            console.error('Error al eliminar usuario:', err);
          }
        }
      };
  
      const getClienteNombre = (idcliente) => {
        const cliente = clientes.value.find(c => c.idcliente === idcliente);
        return cliente ? cliente.nombre : 'N/A';
      };
  
      const getPerfilNombre = (perfilid) => {
        const perfil = perfiles.value.find(p => p.perfil_id === perfilid);
        return perfil ? perfil.perfil_nombre : 'N/A';
      };
  
      const clearForm = () => {
        idcliente.value = '';
        perfilid.value = '';
        nombres.value = '';
        apellidos.value = '';
        usuario.value = '';
        password.value = '';
        errorMessage.value = '';
      };
  
      const cancelEdit = () => {
        clearForm();
        isEditing.value = false;
        editingUserId.value = null;
      };
  
      onMounted(() => {
        fetchClientes();
        fetchPerfiles();
        fetchUsuarios();
      });
  
      return {
        clientes,
        perfiles,
        perfilesFiltrados,
        usuarios,
        idcliente,
        perfilid,
        nombres,
        apellidos,
        usuario,
        password,
        errorMessage,
        isEditing,
        createUser,
        editUser,
        updateUser,
        toggleEstado,
        deleteUser,
        getClienteNombre,
        getPerfilNombre,
        cancelEdit
      };
    }
  };
  </script>
  
  <style scoped>
  .users {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .form-group {
    margin-bottom: 20px;
  }
  
  label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
  }
  
  input,
  select {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
  }
  
  button {
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 10px;
  }
  
  button:hover {
    background-color: #0056b3;
  }
  
  .edit-buttons button[type="button"] {
    background-color: #6c757d;
  }
  
  .edit-buttons button[type="button"]:hover {
    background-color: #5a6268;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 30px;
  }
  
  th,
  td {
    padding: 12px;
    border: 1px solid #ccc;
    text-align: left;
  }
  
  th {
    background-color: #f8f9fa;
    font-weight: bold;
  }
  
  .error-message {
    color: red;
    margin-bottom: 15px;
    font-weight: bold;
  }
  </style>