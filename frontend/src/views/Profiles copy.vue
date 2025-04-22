<template>
    <div class="profiles">
      <h3>Gestión de Perfiles</h3>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <form @submit.prevent="isEditing ? updateProfile() : createProfile()">
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
          <label for="perfil_nombre">Nombre del Perfil:</label>
          <input type="text" id="perfil_nombre" v-model="perfil_nombre" required />
        </div>
        <div class="form-group">
          <label>Permisos:</label>
          <div class="permisos-container">
            <div v-for="seccion in secciones" :key="seccion.name" class="permiso-group">
              <h4>{{ seccion.name }}</h4>
              <div v-for="permiso in seccion.permisos" :key="permiso" class="checkbox-item">
                <label>
                  <input type="checkbox" :value="permiso" v-model="permisos[seccion.name]" />
                  {{ permiso }}
                </label>
              </div>
              <div v-if="seccion.subsecciones" class="subsecciones">
                <div v-for="subseccion in seccion.subsecciones" :key="subseccion.name" class="subseccion">
                  <h5>{{ subseccion.name }}</h5>
                  <div v-for="permiso in subseccion.permisos" :key="permiso" class="checkbox-item">
                    <label>
                      <input type="checkbox" :value="permiso" v-model="permisos[`${seccion.name}_${subseccion.name}`]" />
                      {{ permiso }}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <button v-if="!isEditing" type="submit">Crear Perfil</button>
        <div v-else class="edit-buttons">
          <button type="submit">Guardar</button>
          <button type="button" @click="cancelEdit">Cancelar</button>
        </div>
      </form>
      <h3>Perfiles Existentes</h3>
      <table>
        <thead>
          <tr>
            <th>Cliente</th>
            <th>Nombre</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="perfil in perfiles" :key="perfil.perfil_id">
            <td>{{ getClienteNombre(perfil.idcliente) }}</td>
            <td>{{ perfil.perfil_nombre }}</td>
            <td>
              <button @click="editProfile(perfil)">Editar</button>
              <button @click="deleteProfile(perfil.perfil_id)">Eliminar</button>
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
    name: 'Profiles',
    setup() {
      const store = useStore();
      const clientes = ref([]);
      const perfiles = ref([]);
      const idcliente = ref('');
      const perfil_nombre = ref('');
      const permisos = ref({
        dashboard: [],
        cargue: [],
        parametrizacion: [],
        dashboard_venta_acumulada_pdv: [],
        dashboard_ventas_historicas: [],
        dashboard_rendimiento_mensual: [],
        dashboard_venta_diaria_pdv: [],
        dashboard_ventas_franja_dia: [],
        dashboard_ventas_medio_pago: [],
        dashboard_ventas_producto: [],
        dashboard_ventas_asesor: [],
        cargue_ventas_diarias: [],
        cargue_arqueo: [],
        cargue_venta_mensual_historica: [],
        cargue_presupuesto_venta: [],
        parametrizacion_puntos_de_venta: [],
        parametrizacion_usuarios_y_perfiles: [],
      });
      const errorMessage = ref('');
      const isEditing = ref(false);
      const editingPerfilId = ref(null);
  
      const secciones = [
        {
          name: 'dashboard',
          permisos: ['ver'],
          subsecciones: [
            { name: 'venta_acumulada_pdv', permisos: ['ver'] },
            { name: 'ventas_historicas', permisos: ['ver'] },
            { name: 'rendimiento_mensual', permisos: ['ver'] },
            { name: 'venta_diaria_pdv', permisos: ['ver'] },
            { name: 'ventas_franja_dia', permisos: ['ver'] },
            { name: 'ventas_medio_pago', permisos: ['ver'] },
            { name: 'ventas_producto', permisos: ['ver'] },
            { name: 'ventas_asesor', permisos: ['ver'] },
          ],
        },
        {
          name: 'cargue',
          permisos: ['editar'],
          subsecciones: [
            { name: 'ventas_diarias', permisos: ['editar'] },
            { name: 'arqueo', permisos: ['editar'] },
            { name: 'venta_mensual_historica', permisos: ['editar'] },
            { name: 'presupuesto_venta', permisos: ['editar'] },
          ],
        },
        {
          name: 'parametrizacion',
          permisos: ['editar'],
          subsecciones: [
            { name: 'puntos_de_venta', permisos: ['editar'] },
            { name: 'usuarios_y_perfiles', permisos: ['editar'] },
          ],
        },
      ];
  
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
  
      const fetchPermisos = async (perfil_id) => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const response = await axios.get(`/perfiles/${perfil_id}/permisos`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          const permisosData = response.data;
  
          // Reiniciar permisos
          clearPermisos();
  
          // Cargar permisos
          permisosData.forEach(p => {
            const key = p.subseccion ? `${p.seccion}_${p.subseccion}` : p.seccion;
            if (permisos.value[key] !== undefined) {
              permisos.value[key].push(p.permiso);
            } else {
              console.warn(`Permiso no soportado en frontend: ${key} - ${p.permiso}`);
            }
          });
  
          console.log('Permisos cargados:', permisos.value);
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al obtener permisos';
          console.error('Error al obtener permisos:', err);
        }
      };
  
      const createProfile = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          const perfilResponse = await axios.post(
            '/perfiles',
            { idcliente: idcliente.value, perfil_nombre: perfil_nombre.value },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          const perfil_id = perfilResponse.data.perfil_id;
  
          await savePermisos(perfil_id);
          clearForm();
          fetchPerfiles();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al crear perfil';
          console.error('Error al crear perfil:', err);
        }
      };
  
      const editProfile = async (perfil) => {
        isEditing.value = true;
        editingPerfilId.value = perfil.perfil_id;
        idcliente.value = perfil.idcliente;
        perfil_nombre.value = perfil.perfil_nombre;
        await fetchPermisos(perfil.perfil_id);
      };
  
      const updateProfile = async () => {
        try {
          const token = store.state.auth.token;
          if (!token) throw new Error('No se encontró token de autenticación');
          await axios.put(
            `/perfiles/${editingPerfilId.value}`,
            { idcliente: idcliente.value, perfil_nombre: perfil_nombre.value },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          await savePermisos(editingPerfilId.value);
          clearForm();
          isEditing.value = false;
          editingPerfilId.value = null;
          fetchPerfiles();
        } catch (err) {
          errorMessage.value = err.response?.data?.error || 'Error al actualizar perfil';
          console.error('Error al actualizar perfil:', err);
        }
      };
  
      const deleteProfile = async (perfil_id) => {
        if (confirm('¿Está seguro de eliminar este perfil?')) {
          try {
            const token = store.state.auth.token;
            if (!token) throw new Error('No se encontró token de autenticación');
            await axios.delete(`/perfiles/${perfil_id}`, { headers: { Authorization: `Bearer ${token}` } });
            fetchPerfiles();
          } catch (err) {
            errorMessage.value = err.response?.data?.error || 'Error al eliminar perfil';
            console.error('Error al eliminar perfil:', err);
          }
        }
      };
  
      const savePermisos = async (perfil_id) => {
        const token = store.state.auth.token;
        const permisosToSave = [];
        secciones.forEach(seccion => {
          if (permisos.value[seccion.name]?.length > 0) {
            permisos.value[seccion.name].forEach(permiso => {
              permisosToSave.push({ seccion: seccion.name, subseccion: null, permiso });
            });
          }
          if (seccion.subsecciones) {
            seccion.subsecciones.forEach(subseccion => {
              const key = `${seccion.name}_${subseccion.name}`;
              if (permisos.value[key]?.length > 0) {
                permisos.value[key].forEach(permiso => {
                  permisosToSave.push({ seccion: seccion.name, subseccion: subseccion.name, permiso });
                });
              }
            });
          }
        });
  
        if (permisosToSave.length > 0) {
          await axios.put(
            `/perfiles/${perfil_id}/permisos`,
            permisosToSave,
            { headers: { Authorization: `Bearer ${token}` } }
          );
        }
      };
  
      const getClienteNombre = (idcliente) => {
        const cliente = clientes.value.find(c => c.idcliente === idcliente);
        return cliente ? cliente.nombre : 'N/A';
      };
  
      const clearForm = () => {
        idcliente.value = '';
        perfil_nombre.value = '';
        clearPermisos();
        errorMessage.value = '';
      };
  
      const clearPermisos = () => {
        permisos.value = {
          dashboard: [],
          cargue: [],
          parametrizacion: [],
          dashboard_venta_acumulada_pdv: [],
          dashboard_ventas_historicas: [],
          dashboard_rendimiento_mensual: [],
          dashboard_venta_diaria_pdv: [],
          dashboard_ventas_franja_dia: [],
          dashboard_ventas_medio_pago: [],
          dashboard_ventas_producto: [],
          dashboard_ventas_asesor: [],
          cargue_ventas_diarias: [],
          cargue_arqueo: [],
          cargue_venta_mensual_historica: [],
          cargue_presupuesto_venta: [],
          parametrizacion_puntos_de_venta: [],
          parametrizacion_usuarios_y_perfiles: [],
        };
      };
  
      const cancelEdit = () => {
        clearForm();
        isEditing.value = false;
        editingPerfilId.value = null;
      };
  
      onMounted(() => {
        fetchClientes();
        fetchPerfiles();
      });
  
      return {
        clientes,
        perfiles,
        idcliente,
        perfil_nombre,
        permisos,
        secciones,
        errorMessage,
        isEditing,
        createProfile,
        editProfile,
        updateProfile,
        deleteProfile,
        cancelEdit,
        getClienteNombre,
      };
    },
  };
  </script>
  
  <style scoped>
  .profiles {
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
  
  .permisos-container {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
  }
  
  .permiso-group {
    margin: 15px 0;
    padding: 10px;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .checkbox-item {
    margin: 5px 0;
  }
  
  .subsecciones {
    margin-left: 20px;
  }
  
  .subseccion {
    margin: 10px 0;
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