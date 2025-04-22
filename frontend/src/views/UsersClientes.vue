<template>
    <div class="users-clientes">
      <h3>Gestión de Usuarios</h3>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <form @submit.prevent="isEditing ? updateUser() : createUser()" class="form-grid">
        <div class="form-group">
          <label for="nombre">Nombre:</label>
          <input type="text" id="nombre" v-model="nombre" required />
        </div>
        <div class="form-group">
          <label for="apellidos">Apellidos:</label>
          <input type="text" id="apellidos" v-model="apellidos" />
        </div>
        <div class="form-group">
          <label for="usuario">Usuario:</label>
          <input type="text" id="usuario" v-model="usuario" required />
        </div>
        <div class="form-group">
          <label for="password">Contraseña:</label>
          <input type="password" id="password" v-model="password" :required="!isEditing" />
        </div>
        <div class="form-group">
          <label for="perfil_id">Perfil:</label>
          <select id="perfil_id" v-model="perfil_id" required>
            <option value="">Seleccione un perfil</option>
            <option v-for="perfil in perfiles" :key="perfil.perfil_id" :value="perfil.perfil_id">
              {{ perfil.perfil_nombre }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="estado">Estado:</label>
          <select id="estado" v-model="estado">
            <option :value="true">Activo</option>
            <option :value="false">Inactivo</option>
          </select>
        </div>
        <div class="button-group">
          <button v-if="!isEditing" type="submit">Crear Usuario</button>
          <div v-else>
            <button type="submit">Guardar</button>
            <button type="button" @click="cancelEdit">Cancelar</button>
          </div>
        </div>
      </form>
      <h3>Usuarios Existentes</h3>
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Apellidos</th>
            <th>Usuario</th>
            <th>Perfil</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in usuarios" :key="user.idusuario">
            <td>{{ user.nombre }}</td>
            <td>{{ user.apellidos }}</td>
            <td>{{ user.usuario }}</td>
            <td>{{ getPerfilNombre(user.perfil_id) }}</td>
            <td>{{ user.estado ? 'Activo' : 'Inactivo' }}</td>
            <td>
              <button @click="editUser(user)">Editar</button>
              <button @click="deleteUser(user.idusuario)">Eliminar</button>
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
    name: 'UsersClientes',
    setup() {
      const store = useStore();
      const usuarios = ref([]);  // Definido como "usuarios"
      const perfiles = ref([]);
      const nombre = ref('');
      const apellidos = ref('');
      const usuario = ref('');
      const password = ref('');
      const perfil_id = ref('');
      const estado = ref(true);
      const errorMessage = ref('');
      const isEditing = ref(false);
      const editingUserId = ref(null);
  
      const fetchUsers = async () => {
        try {
          const token = store.state.auth.token;
          const idcliente = store.state.auth.idcliente;
          if (!token || !idcliente) throw new Error('Autenticación inválida');
          const response = await axios.get('/usuarios', { headers: { Authorization: `Bearer ${token}` } });
          usuarios.value = response.data.filter(user => user.idcliente === idcliente);  // Cambiado a usuarios.value
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener usuarios';
          console.error('Error al obtener usuarios:', err);
        }
      };
  
      const fetchPerfiles = async () => {
        try {
          const token = store.state.auth.token;
          const idcliente = store.state.auth.idcliente;
          if (!token || !idcliente) throw new Error('Autenticación inválida');
          const response = await axios.get('/perfiles', { headers: { Authorization: `Bearer ${token}` } });
          perfiles.value = response.data.filter(perfil => perfil.idcliente === idcliente);
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener perfiles';
          console.error('Error al obtener perfiles:', err);
        }
      };
  
      const createUser = async () => {
        try {
          const token = store.state.auth.token;
          const idcliente = store.state.auth.idcliente;
          if (!token || !idcliente) throw new Error('Autenticación inválida');
          await axios.post(
            '/usuarios',
            { idcliente, nombre: nombre.value, apellidos: apellidos.value, usuario: usuario.value, password: password.value, perfil_id: perfil_id.value, estado: estado.value },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          fetchUsers();
        } catch (err) {
          if (err.response?.data?.error.includes("nombre de usuario ya está en uso")) {
            errorMessage.value = err.response.data.error;
          } else {
            errorMessage.value = err.response?.data?.error || 'Error al crear usuario';
          }
          console.error('Error al crear usuario:', err);
        }
      };
  
      const editUser = (user) => {
        isEditing.value = true;
        editingUserId.value = user.idusuario;
        nombre.value = user.nombre;
        apellidos.value = user.apellidos;  // Corregido: asignar a .value
        usuario.value = user.usuario;
        password.value = ''; // Contraseña vacía al editar por seguridad
        perfil_id.value = user.perfil_id;
        estado.value = user.estado;
      };
  
      const updateUser = async () => {
        try {
          const token = store.state.auth.token;
          const idcliente = store.state.auth.idcliente;
          if (!token || !idcliente) throw new Error('Autenticación inválida');
          const data = { idcliente, nombre: nombre.value, apellidos: apellidos.value, usuario: usuario.value, perfil_id: perfil_id.value, estado: estado.value };
          if (password.value) data.password = password.value;
          await axios.put(
            `/usuarios/${editingUserId.value}`,
            data,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          clearForm();
          isEditing.value = false;
          editingUserId.value = null;
          fetchUsers();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al actualizar usuario';
          console.error('Error al actualizar usuario:', err);
        }
      };
  
      const deleteUser = async (idusuario) => {
        if (confirm('¿Está seguro de eliminar este usuario?')) {
          try {
            const token = store.state.auth.token;
            if (!token) throw new Error('No se encontró token de autenticación');
            await axios.delete(`/usuarios/${idusuario}`, { headers: { Authorization: `Bearer ${token}` } });
            fetchUsers();
          } catch (err) {
            errorMessage.value = err.response?.data?.error || 'Error al eliminar usuario';
            console.error('Error al eliminar usuario:', err);
          }
        }
      };
  
      const getPerfilNombre = (perfil_id) => {
        const perfil = perfiles.value.find(p => p.perfil_id === perfil_id);
        return perfil ? perfil.perfil_nombre : 'N/A';
      };
  
      const clearForm = () => {
        nombre.value = '';
        apellidos.value = '';
        usuario.value = '';
        password.value = '';
        perfil_id.value = '';
        estado.value = true;
        errorMessage.value = '';
      };
  
      const cancelEdit = () => {
        clearForm();
        isEditing.value = false;
        editingUserId.value = null;
      };
  
      onMounted(() => {
        fetchUsers();
        fetchPerfiles();
      });
  
      return {
        usuarios,  // Cambiado de "users" a "usuarios"
        perfiles,
        nombre,
        apellidos,
        usuario,
        password,
        perfil_id,
        estado,
        errorMessage,
        isEditing,
        createUser,
        editUser,
        updateUser,
        deleteUser,
        cancelEdit,
        getPerfilNombre,
      };
    },
  };
  </script>
  
  <style scoped>
  .users-clientes {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .form-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 20px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
  }
  
  label {
    margin-bottom: 5px;
    font-weight: bold;
  }
  
  input,
  select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  .button-group {
    grid-column: span 3;
    display: flex;
    justify-content: center;
    gap: 10px;
  }
  
  button {
    padding: 10px 20px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:hover {
    background-color: #2c3e50;
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
    font-weight: bold;
  }
  
  .error-message {
    color: red;
    margin-bottom: 15px;
  }
  </style>