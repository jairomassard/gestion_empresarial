import { createStore } from 'vuex';
import axios from '@/api/axios';

export default createStore({
  state: {
    auth: {
      token: null,
      idcliente: null,
      perfilid: null,
      permisos: []
    },
    cliente: {
      nombre: '',
      logo: '',
      estado: true
    }
  },
  mutations: {
    setAuth(state, { token, idcliente, perfilid, permisos }) {
      state.auth.token = token;
      state.auth.idcliente = idcliente;
      state.auth.perfilid = perfilid;
      state.auth.permisos = permisos;
    },
    setCliente(state, { nombre, logo, estado }) {
      state.cliente.nombre = nombre;
      state.cliente.logo = logo;
      state.cliente.estado = estado !== undefined ? estado : true;
    },
    logout(state) {
      state.auth.token = null;
      state.auth.idcliente = null;
      state.auth.perfilid = null;
      state.auth.permisos = [];
      state.cliente.nombre = '';
      state.cliente.logo = '';
      state.cliente.estado = true;
    }
  },
  actions: {
    async fetchCliente({ commit, state }) {
      if (!state.auth.idcliente) {
        console.error('No idcliente available for fetchCliente');
        return;
      }
      try {
        console.log(`Fetching cliente data for idcliente: ${state.auth.idcliente}`);
        const response = await axios.get(`/cliente/${state.auth.idcliente}`, {
          headers: { Authorization: `Bearer ${state.auth.token}` }
        });
        console.log('fetchCliente response:', response.data);
        commit('setCliente', {
          nombre: response.data.nombre || '',
          logo: response.data.logo || '',
          estado: response.data.estado !== undefined ? response.data.estado : true
        });
      } catch (err) {
        console.error('Error fetching cliente:', err.response?.data || err.message);
        throw err; // Re-lanzar para que router.beforeEach maneje el error
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.auth.token,
    isSuperAdmin: state => state.auth.perfilid === 1,
    hasPermission: state => (seccion, subseccion, permiso) => {
      if (state.auth.perfilid === 1) {
        console.log('Superadmin access granted');
        return true; // Superadmin tiene acceso total
      }
      const hasPerm = state.auth.permisos.some(p =>
        p.seccion === seccion &&
        (p.subseccion === subseccion || (!subseccion && !p.subseccion)) &&
        (p.permiso === permiso || (permiso === 'ver' && p.permiso === 'editar'))
      );
      console.log(`Checking permission: ${seccion}/${subseccion}/${permiso} -> ${hasPerm}`);
      return hasPerm;
    }
  }
});
