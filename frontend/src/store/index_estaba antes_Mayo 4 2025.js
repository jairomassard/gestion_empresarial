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
      estado: true  // Añadimos estado con valor por defecto true
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
      state.cliente.estado = estado !== undefined ? estado : true; // Manejamos el caso donde estado no se envíe
    },
    logout(state) {
      state.auth.token = null;
      state.auth.idcliente = null;
      state.auth.perfilid = null;
      state.auth.permisos = [];
      state.cliente.nombre = '';
      state.cliente.logo = '';
      state.cliente.estado = true; // Restablecemos estado a true
    }
  },
  actions: {
    async fetchCliente({ commit, state }) {
      if (!state.auth.idcliente) return;
      try {
        const response = await axios.get(`/cliente/${state.auth.idcliente}`, {  // Ajusté a /cliente/<idcliente> según tu backend
          headers: { Authorization: `Bearer ${state.auth.token}` }
        });
        commit('setCliente', {
          nombre: response.data.nombre,
          logo: response.data.logo,
          estado: response.data.estado  // Añadimos estado
        });
      } catch (err) {
        console.error('Error al obtener información del cliente:', err);
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.auth.token,
    isSuperAdmin: state => state.auth.perfilid === 1,
    hasPermission: state => (seccion, subseccion, permiso) => {
      return state.auth.permisos.some(p =>
        p.seccion === seccion &&
        (p.subseccion === subseccion || (!subseccion && !p.subseccion)) &&
        p.permiso === permiso
      );
    }
  }
});
