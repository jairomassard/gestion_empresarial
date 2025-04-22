<template>
    <div class="reportes-produccion">
      <h1 class="main-title"><font-awesome-icon icon="chart-bar" /> Reportes de Producción</h1>
      <h2 class="cliente-nombre" v-if="store.state.cliente.nombre">
        {{ store.state.cliente.nombre }}
      </h2>
  
      <!-- Botones de navegación -->

      <div class="actions" style="justify-content: flex-end">
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
      </div>

      <!-- Filtros -->
      <section class="section filter-section">
        <h2 class="section-title">Consultar Órdenes</h2>
        <div class="filter-container">
          <div class="filter-group">
            <label for="numero-orden" class="filter-label">Número de Orden:</label>
            <input
              type="text"
              id="numero-orden"
              class="filter-input"
              v-model="filtroNumeroOrden"
              placeholder="Ej: ORDEN-123"
            />
          </div>
          <div class="filter-group">
            <label for="estado" class="filter-label">Estado:</label>
            <select v-model="filtroEstado" id="estado" class="filter-select">
              <option value="">Todos</option>
              <option value="Pendiente">Pendiente</option>
              <option value="Lista para Producción">Lista para Producción</option>
              <option value="En Producción">En Producción</option>
              <option value="En Producción-Parcial">En Producción-Parcial</option>
              <option value="Finalizada">Finalizada</option>
            </select>
          </div>
          <div class="filter-group">
            <label for="fecha-inicio" class="filter-label">Fecha Inicio:</label>
            <input type="date" id="fecha-inicio" class="filter-input" v-model="filtroFechaInicio" />
          </div>
          <div class="filter-group">
            <label for="fecha-fin" class="filter-label">Fecha Fin:</label>
            <input type="date" id="fecha-fin" class="filter-input" v-model="filtroFechaFin" />
          </div>
        </div>
        <p class="filter-note">
          Nota: Para incluir órdenes del día actual, seleccione un día adicional para Fecha Fin.
        </p>
        <div class="filter-actions">
          <button class="action-button search-button" @click="consultarOrdenes">
            <font-awesome-icon icon="search" /> Consultar
          </button>
          <button class="action-button pdf-button" @click="imprimirListadoPdf" :disabled="ordenes.length === 0">
            <font-awesome-icon icon="file-pdf" /> Imprimir Listado
          </button>
        </div>
      </section>
  
      <!-- Tabla de órdenes -->
      <section v-if="ordenes.length > 0" class="section table-section">
        <h2 class="section-title">Órdenes de Producción</h2>
        <div class="table-container">
          <table class="custom-table">
            <thead>
              <tr>
                <th>Número de Orden</th>
                <th>Producto</th>
                <th>Cantidad a Producir</th>
                <th>Estado</th>
                <th>Fecha Estado</th>
                <th>Tiempo en Producción</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="orden in ordenes" :key="orden.id">
                <td>{{ orden.numero_orden }}</td>
                <td>{{ orden.producto_compuesto_nombre }}</td>
                <td>{{ orden.cantidad_paquetes.toFixed(2) }}</td>
                <td>{{ orden.estado }}</td>
                <td>{{ obtenerFechaEstado(orden) }}</td>
                <td>{{ calcularTiempoProduccion(orden) }}</td>
                <td>
                  <button class="table-button detail-button" @click="cargarDetalleOrden(orden.id)">
                    <font-awesome-icon icon="eye" /> Detalle
                  </button>
                  <button class="table-button pdf-button" @click="descargarPdf(orden.id)">
                    <font-awesome-icon icon="file-pdf" /> Imprimir
                  </button>
                  <button class="table-button pdf-no-cost-button" @click="descargarPdfOperador(orden.id)">
                    <font-awesome-icon icon="file-pdf" /> Sin Costos
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
  
      <!-- Mensaje si no hay órdenes -->
      <p v-if="consultaRealizada && ordenes.length === 0 && (filtroEstado || filtroNumeroOrden || filtroFechaInicio)" class="error-message">
        No se encontraron órdenes de producción con los filtros seleccionados.
      </p>
  
      <!-- Detalle de la orden -->
      <section v-if="mostrarDetalle" class="section detail-section">
        <h2 class="section-title">Detalle de la Orden</h2>
        <div class="detail-container">
          <div class="detail-actions">
            <button class="action-button pdf-button" @click="descargarPdf(detalleOrden.id)">
              <font-awesome-icon icon="file-pdf" /> Imprimir
            </button>
            <button class="action-button pdf-no-cost-button" @click="descargarPdfOperador(detalleOrden.id)">
              <font-awesome-icon icon="file-pdf" /> Imprimir Sin Costos
            </button>
          </div>
  
          <!-- Información general -->
          <div class="info-general-card">
            <p><strong>Número de Orden:</strong> {{ detalleOrden?.numero_orden || 'N/A' }}</p>
            <p><strong>Producto:</strong> {{ detalleOrden?.producto_compuesto_nombre || 'N/A' }}</p>
            <p><strong>Cantidad de Paquetes:</strong> {{ detalleOrden?.cantidad_paquetes?.toFixed(2) || 'N/A' }}</p>
            <p><strong>Bodega de Producción:</strong> {{ detalleOrden?.bodega_produccion_nombre || 'No especificada' }}</p>
            <p><strong>Estado:</strong> {{ detalleOrden?.estado || 'N/A' }}</p>
          </div>
  
          <!-- Tabla de costos -->
          <table class="custom-table">
            <tbody>
              <tr>
                <td class="table-label">Costo Unitario</td>
                <td>{{ detalleOrden?.costo_unitario?.toFixed(2) || 'N/A' }}</td>
                <td class="table-label">Costo Total</td>
                <td>{{ detalleOrden?.costo_total?.toFixed(2) || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
  
          <!-- Tabla de fechas -->
          <table class="custom-table">
            <thead>
              <tr>
                <th colspan="4">-- Fechas de Producción --</th>
              </tr>
              <tr>
                <th>Creación</th>
                <th>Lista para Producción</th>
                <th>Inicio Producción</th>
                <th>Finalización</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{{ formatFecha(detalleOrden?.fecha_creacion) }}</td>
                <td>{{ formatFecha(detalleOrden?.fecha_lista_para_produccion) }}</td>
                <td>{{ formatFecha(detalleOrden?.fecha_inicio) }}</td>
                <td>{{ formatFecha(detalleOrden?.fecha_finalizacion) }}</td>
              </tr>
            </tbody>
          </table>
  
          <!-- Tabla de responsables -->
          <table class="custom-table">
            <tbody>
              <tr>
                <td class="table-label">Creado por</td>
                <td>{{ detalleOrden?.creado_por || 'N/A' }}</td>
                <td class="table-label">Producido por</td>
                <td>{{ detalleOrden?.producido_por || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
  
          <!-- Tabla de componentes -->
          <h3 class="section-subtitle">Componentes</h3>
          <table class="custom-table">
            <thead>
              <tr>
                <th>Componente</th>
                <th>Cant. x Paquete</th>
                <th>Cant. Total</th>
                <th>Peso x Paquete</th>
                <th>Peso Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="componente in componentes" :key="componente.nombre">
                <td>{{ componente.nombre }}</td>
                <td>{{ componente.cant_x_paquete.toFixed(2) }}</td>
                <td>{{ componente.cantidad_total.toFixed(2) }}</td>
                <td>{{ componente.peso_x_paquete.toFixed(2) }}</td>
                <td>{{ componente.peso_total.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
  
          <!-- Historial de Entregas -->
          <h3 class="section-subtitle">Historial de Entregas</h3>
          <table v-if="historialEntregas.length > 0" class="custom-table">
            <thead>
              <tr>
                <th>Cantidad Entregada</th>
                <th>Fecha y Hora</th>
                <th>Comentario</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entrega in historialEntregas" :key="entrega.id">
                <td>{{ entrega.cantidad.toFixed(2) }}</td>
                <td>{{ formatFecha(entrega.fecha_hora) }}</td>
                <td>{{ entrega.comentario || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="text-muted">No hay entregas registradas para esta orden.</p>
  
          <!-- Comentario de cierre forzado o finalización -->
          <div v-if="detalleOrden?.comentario_cierre_forzado" class="detail-section">
            <h3 class="section-subtitle">Cierre Forzado</h3>
            <p>{{ detalleOrden.comentario_cierre_forzado }}</p>
          </div>
          <div v-else-if="detalleOrden?.estado === 'Finalizada'" class="detail-section">
            <h3 class="section-subtitle">Orden Finalizada sin Novedad</h3>
          </div>
        </div>
      </section>
    </div>
  </template>
  
  <script>
  import { useStore } from 'vuex';
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
  import apiClient from '@/api/axios';
  import { toast } from 'vue3-toastify';
  
  export default {
    name: 'ReportesProduccion',
    components: { FontAwesomeIcon },
    setup() {
      const store = useStore();
      return { store, toast };
    },
    data() {
      return {
        filtroNumeroOrden: '',
        filtroEstado: '',
        filtroFechaInicio: '',
        filtroFechaFin: '',
        ordenes: [],
        detalleOrden: null,
        componentes: [],
        historialEntregas: [],
        mostrarDetalle: false,
        consultaRealizada: false,
      };
    },
    methods: {
      formatFecha(fecha) {
        if (!fecha) return 'N/A';
        const fechaObj = new Date(fecha);
        return fechaObj.toLocaleString('es-CO', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        });
      },
      limpiarPagina() {
        this.filtroNumeroOrden = '';
        this.filtroEstado = '';
        this.filtroFechaInicio = '';
        this.filtroFechaFin = '';
        this.ordenes = [];
        this.detalleOrden = null;
        this.componentes = [];
        this.historialEntregas = [];
        this.mostrarDetalle = false;
        this.consultaRealizada = false;
        this.toast.success('Página limpiada correctamente.');
      },
      calcularTiempoProduccion(orden) {
        if (!orden.fecha_creacion) return 'N/A';
        let fechaReferencia = orden.fecha_finalizacion || orden.fecha_inicio || orden.fecha_lista_para_produccion || orden.fecha_creacion;
        if (!fechaReferencia) return 'N/A';
        let fechaCreacion = new Date(orden.fecha_creacion);
        let fechaUltimoEstado = new Date(fechaReferencia);
        let diferenciaMs = fechaUltimoEstado - fechaCreacion;
        let diferenciaHoras = diferenciaMs / (1000 * 60 * 60);
        if (diferenciaHoras >= 24) {
          let diferenciaDias = Math.floor(diferenciaHoras / 24);
          return `${diferenciaDias} día(s)`;
        } else {
          return `${Math.floor(diferenciaHoras)} hora(s)`;
        }
      },
      obtenerFechaEstado(orden) {
        switch (orden.estado) {
          case 'Pendiente':
            return this.formatFecha(orden.fecha_creacion);
          case 'Lista para Producción':
            return this.formatFecha(orden.fecha_lista_para_produccion);
          case 'En Producción':
          case 'En Producción-Parcial':
            return this.formatFecha(orden.fecha_inicio);
          case 'Finalizada':
            return this.formatFecha(orden.fecha_finalizacion);
          default:
            return 'N/A';
        }
      },
      async consultarOrdenes() {
        if (!this.filtroNumeroOrden && !this.filtroEstado && !this.filtroFechaInicio && !this.filtroFechaFin) {
          this.toast.warning('Por favor, ingrese al menos un filtro para consultar.');
          return;
        }
        try {
          const params = {};
          if (this.filtroNumeroOrden) params.numero_orden = this.filtroNumeroOrden;
          params.estado = this.filtroEstado || null;
          if (this.filtroFechaInicio && this.filtroFechaFin) {
            params.fecha_inicio = this.filtroFechaInicio;
            params.fecha_fin = this.filtroFechaFin;
          }
          const response = await apiClient.get('/api/ordenes-produccion/filtrar', { params });
          this.ordenes = response.data.sort((a, b) => b.id - a.id);
          this.consultaRealizada = true;
          this.mostrarDetalle = false;
          this.detalleOrden = null;
          this.componentes = [];
          this.historialEntregas = [];
          this.toast.success('Órdenes consultadas correctamente.');
        } catch (error) {
          console.error('Error al consultar órdenes:', error.response?.status, error.response?.data, error.message);
          this.consultaRealizada = true;
          this.toast.error('No se pudieron consultar las órdenes de producción.');
        }
      },
      async imprimirListadoPdf() {
        try {
          const params = {
            estado: this.filtroEstado || null,
            fecha_inicio: this.filtroFechaInicio || null,
            fecha_fin: this.filtroFechaFin || null,
          };
          const response = await apiClient.post('/api/ordenes-produccion/listado-pdf', params, {
            responseType: 'blob',
          });
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', 'Listado_Ordenes_Produccion.pdf');
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          this.toast.success('PDF generado correctamente.');
        } catch (error) {
          console.error('Error al generar PDF:', error);
          this.toast.error('No se pudo generar el PDF del listado.');
        }
      },
      async cargarDetalleOrden(ordenId) {
        try {
          console.log(`Cargando detalle para orden ID: ${ordenId}`);
          const detalleResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}`);
          console.log('Respuesta de detalle:', detalleResponse.data);
          this.detalleOrden = {
            ...detalleResponse.data,
            bodega_produccion_nombre: detalleResponse.data.bodega_produccion_nombre || 'No especificada',
            creado_por: detalleResponse.data.creado_por || 'N/A',
            producido_por: detalleResponse.data.producido_por || 'N/A',
          };
          this.componentes = detalleResponse.data.materiales?.map((componente) => ({
            nombre: componente.producto_base_nombre,
            cant_x_paquete: componente.cant_x_paquete,
            cantidad_total: componente.cantidad_total,
            peso_x_paquete: componente.peso_x_paquete,
            peso_total: componente.peso_total,
          })) || [];
          const historialResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}/historial-entregas`);
          console.log('Respuesta de historial:', historialResponse.data);
          this.historialEntregas = historialResponse.data.historial || [];
          this.mostrarDetalle = true;
          this.toast.success('Detalle de la orden cargado correctamente.');
        } catch (error) {
          console.error('Error al cargar detalle:', error.response?.status, error.response?.data, error.message);
          this.toast.error(`No se pudo cargar el detalle de la orden: ${error.message}`);
          this.mostrarDetalle = false;
        }
      },
      async descargarPdf(ordenId) {
        if (!ordenId) {
          this.toast.error('El ID de la orden no está disponible.');
          return;
        }
        try {
          const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf`, {
            responseType: 'blob',
          });
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `Orden_${ordenId}.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          this.toast.success('PDF descargado correctamente.');
        } catch (error) {
          console.error('Error al descargar PDF:', error);
          this.toast.error('No se pudo descargar el PDF de la orden.');
        }
      },
      async descargarPdfOperador(ordenId) {
        if (!ordenId) {
          this.toast.error('El ID de la orden no está disponible.');
          return;
        }
        try {
          const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf-operador`, {
            responseType: 'blob',
          });
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `Orden_${ordenId}_Operador.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          this.toast.success('PDF sin costos descargado correctamente.');
        } catch (error) {
          console.error('Error al descargar PDF operador:', error);
          this.toast.error('No se pudo descargar el PDF sin costos.');
        }
      },
      volverAlMenu() {
        const tipoUsuario = localStorage.getItem('tipo_usuario');
        if (tipoUsuario === 'admin') {
          this.$router.push('/production');
        } else if (tipoUsuario === 'gerente') {
          this.$router.push('/production');
        } else if (tipoUsuario === 'operador') {
          this.$router.push('/production');
        } else {
          this.toast.error('Rol no reconocido. Contacta al administrador.');
          this.$router.push('/login');
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .reportes-produccion {
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  
  .cliente-nombre {
    font-size: 1.5rem;
    color: #34495e;
    text-align: center;
    margin-bottom: 30px;
  }
  
  .actions-container {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
  }
  .form-actions {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
    }
  .action-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 15px;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    color: #fff;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }
  button {
  padding: 0.6rem 1.2rem;
  border: none;
  background-color: #42b983;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  
}

button:hover {
  background-color: #2c3e50;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
}

button.btn-warning {
  background-color: #ffc107;
  color: #333;
}

button.btn-warning:hover {
  background-color: #e0a800;
}
  
  .back-button {
    background-color: #6c757d;
  }
  
  .back-button:hover {
    background-color: #5a6268;
  }
  
  .clear-button {
    background-color: #ffc107;
  }
  
  .clear-button:hover {
    background-color: #e0a800;
  }

  button.btn-warning {
    background-color: #ffc107;
    color: #333;
    }

    button.btn-warning:hover {
    background-color: #e0a800;
    }
    
  .search-button {
    background-color: #42b983;
  }
  
  .search-button:hover {
    background-color: #2c3e50;
  }
  
  .pdf-button {
    background-color: #42b983;
  }
  
  .pdf-button:hover {
    background-color: #2c3e50;
  }
  
  .section {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .section-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 20px;
  }
  
  .section-subtitle {
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
    margin-top: 20px;
    margin-bottom: 10px;
  }
  
  .filter-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .filter-group {
    display: flex;
    flex-direction: column;
  }
  
  .filter-label {
    font-size: 1rem;
    color: #34495e;
    margin-bottom: 5px;
  }
  
  .filter-input,
  .filter-select {
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 0.9rem;
    color: #34495e;
  }
  
  .filter-note {
    font-size: 0.9rem;
    color: #6c757d;
    margin-bottom: 15px;
  }
  
  .filter-actions {
    display: flex;
    gap: 15px;
  }
  
  .table-container {
    overflow-x: auto;
  }
  
  .custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    color: #34495e;
  }
  
  .custom-table th,
  .custom-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }
  
  .custom-table th {
    background-color: #f9f9f9;
    font-weight: 600;
  }
  
  .custom-table tr:hover {
    background-color: #e0e7ff;
  }
  
  .table-label {
    font-weight: 600;
    background-color: #f9f9f9;
  }
  
  .table-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border: none;
    border-radius: 8px;
    font-size: 0.8rem;
    color: #fff;
    cursor: pointer;
    margin-right: 5px;
    transition: background-color 0.2s ease;
  }
  
  .detail-button {
    background-color: #42b983;
  }
  
  .detail-button:hover {
    background-color: #2c3e50;
  }
  
  .pdf-no-cost-button {
    background-color: #42b983;
  }
  
  .pdf-no-cost-button:hover {
    background-color: #2c3e50;
  }
  
  .error-message {
    color: #dc3545;
    font-size: 1rem;
    text-align: center;
    margin: 20px 0;
  }
  
  /* Estilos para info-general-card */
    .info-general-card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    width: 100%; /* Asegura que use todo el ancho disponible */
    max-width: 1300px; /* Limita el ancho máximo */
    }

    /* Estilos para filas */
    .info-row1 {
    display: grid;
    gap: 15px;
    margin-bottom: 15px;
    }

    .info-row1 {
    display: grid;
    gap: 15px;
    margin-bottom: 15px;
    }


  .info-general p {
    margin: 0.5rem 0;
    font-size: 1rem;
    color: #34495e;
  }
  
  .info-general strong {
    color: #2c3e50;
  }
  
  .detail-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .detail-actions {
    display: flex;
    gap: 15px;
  }
  
  .text-muted {
    color: #6c757d;
    font-size: 0.9rem;
  }
  
  @media (max-width: 768px) {
    .main-title {
      font-size: 1.5rem;
    }
  
    .cliente-nombre {
      font-size: 1.2rem;
    }
  
    .section-title {
      font-size: 1.2rem;
    }
  
    .filter-container {
      grid-template-columns: 1fr;
    }
  
    .custom-table {
      font-size: 0.8rem;
    }
  
    .table-button {
      padding: 6px 10px;
      font-size: 0.7rem;
    }
  }
  </style>