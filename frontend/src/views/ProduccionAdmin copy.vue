<template>
    <div class="produccion-admin">
      <h1>Módulo de Producción</h1>
  
      <div class="actions" style="justify-content: flex-end">
        
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
      </div>
  
      <!-- Crear nueva orden de producción -->
      <section>
        <h2>Crear Orden de Producción</h2>
        <form @submit.prevent="revisarOrden">
          <!-- Campo de búsqueda por nombre -->
          <label for="nombreProducto">Buscar por nombre:</label>
          <input 
            type="text" 
            id="nombreProducto"
            v-model="nombreProductoCompuesto"
            placeholder="Ingrese nombre del producto"
            class="form-control"
            @input="sincronizarPorNombre"
          />
  
          <!-- Campo de búsqueda por código -->
          <label for="codigoProducto">Código del Producto:</label>
          <input 
            type="text" 
            id="codigoProducto" 
            v-model="codigoProductoCompuesto" 
            placeholder="Ingrese el código del producto compuesto"
            @input="sincronizarCodigoConSelector"
          />
  
          <!-- Selector de productos -->
          <label for="producto">Producto Compuesto:</label>
          <select v-model="nuevaOrden.producto_compuesto_id" @change="sincronizarSelectorConCodigo" required>
            <option value="" disabled>Seleccione un producto</option>
            <option v-for="producto in productosCompuestos" :key="producto.id" :value="producto.id">
              {{ producto.codigo }} - {{ producto.nombre }}
            </option>
          </select>
  
          <br>
          <label for="cantidad">Cantidad de Paquetes a Producir:</label>
          <input type="number" v-model="nuevaOrden.cantidad_paquetes" required min="1" />
  
          <!-- Selector de bodega de producción -->
          <label for="bodegaProduccion">Bodega de Producción:</label>
          <select v-model="nuevaOrden.bodega_produccion" required>
            <option value="" disabled>Seleccione una bodega</option>
            <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.id">
              {{ bodega.nombre }}
            </option>
          </select>
  
          <br>
          <button type="submit">Revisar</button>
        </form>
      </section>
  
      <!-- Tabla de revisión -->
      <section v-if="tablaRevisarVisible">
        <h3>Revisión de Componentes</h3>
        <table>
          <thead>
            <tr>
              <th>Componentes</th>
              <th>Cant. x Paquete</th>
              <th>Cant. a Producir</th>
              <th>Cant. Total Req.</th>
              <th>Peso Unitario</th>
              <th>Peso Total</th>
              <th>Costo Unitario</th>
              <th>Costo Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="componente in componentes" :key="componente.id">
              <td>{{ componente.nombre }}</td>
              <td>{{ componente.cantidad_requerida }}</td>
              <td>{{ nuevaOrden.cantidad_paquetes }}</td>
              <td>{{ componente.cantidad_total.toFixed(2) }}</td>
              <td>{{ componente.peso_unitario }}</td>
              <td>{{ componente.peso_total.toFixed(2) }}</td>
              <td>${{ componente.costo_unitario.toFixed(2) }}</td>
              <td>${{ componente.costo_total.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
  
        <button @click="crearOrden">Crear Orden</button>
      </section>
  
      <!-- Consultar órdenes de producción -->
      <section>
        <h2>Órdenes de Producción</h2>
  
        <!-- Filtros -->
        <div>
          <label for="numero-orden">Número de Orden:</label>
          <input
            type="text"
            id="numero-orden"
            v-model="filtroNumeroOrden"
            placeholder="Ingrese el número de orden"
          />
  
          <label for="estado">Estado:</label>
          <select v-model="filtroEstado" id="estado">
            <option value="">Todos</option>
            <option value="Pendiente">Pendiente</option>
            <option value="Lista para Producción">Lista para Producción</option>
            <option value="En Producción">En Producción</option>
            <option value="En Producción-Parcial">En Producción-Parcial</option>
            <option value="Finalizada">Finalizada</option>
          </select>
          <br>
          <button @click="consultarOrdenes">Consultar</button>
        </div>
  
        <!-- Tabla de órdenes de producción -->
        <table v-if="ordenes.length > 0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Número de Orden</th>
              <th>Producto</th>
              <th>Cantidad a Producir</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="orden in ordenes" :key="orden.id">
              <td>{{ orden.id }}</td>
              <td>{{ orden.numero_orden }}</td>
              <td>{{ orden.producto_compuesto_nombre }}</td>
              <td>{{ orden.cantidad_paquetes }}</td>
              <td>{{ orden.estado }}</td>
              <td>
                <button v-if="orden.estado === 'Pendiente'" @click="actualizarEstado(orden.id, 'Lista para Producción')">
                  Marcar Lista para Producción
                </button>
                <button v-if="orden.estado === 'Lista para Producción'" @click="actualizarEstado(orden.id, 'En Producción')">
                  Iniciar Producción
                </button>
                <button v-if="orden.estado === 'En Producción' || orden.estado === 'En Producción-Parcial'" @click="registrarProduccion(orden.id)">
                  Registrar Producción
                </button>
                <button v-if="orden.estado === 'Pendiente' || orden.estado === 'Lista para Producción'"
                        @click="eliminarOrden(orden.id)" class="btn btn-danger">
                  Eliminar Orden
                </button>
                <button @click="cargarDetalleOrden(orden.id)">Detalle</button>
                <button @click="descargarPdf(orden.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button>
                <button @click="descargarPdfOperador(orden.id)">Imprimir Sin costos <i class="fas fa-file-pdf pdf-icon"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
  
        <p v-if="ordenes.length === 0">No se encontraron órdenes de producción.</p>
      </section>
  
      <section v-if="tablaDetalleVisible" class="detalle-orden">
        <h2>Detalle de la Orden</h2>
        <div class="acciones-orden">
          <!-- Botones condicionales -->
          <button v-if="detalleOrden?.estado === 'Pendiente'" @click="actualizarEstado(detalleOrden.id, 'Lista para Producción')">
            Marcar Lista para Producción
          </button>
          <button v-if="detalleOrden?.estado === 'Lista para Producción'" @click="actualizarEstado(detalleOrden.id, 'En Producción')">
            Iniciar Producción
          </button>
          <button v-if="detalleOrden?.estado === 'En Producción' || detalleOrden?.estado === 'En Producción-Parcial'" @click="registrarProduccion(detalleOrden.id)">
            Registrar Producción
          </button>
          <button v-if="detalleOrden?.estado === 'Pendiente' || detalleOrden?.estado === 'Lista para Producción'" @click="eliminarOrden(detalleOrden.id)" class="btn btn-danger">
            Eliminar Orden
          </button>
          <button @click="descargarPdf(detalleOrden?.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button>
          <button @click="descargarPdfOperador(detalleOrden?.id)">Imprimir Sin costos <i class="fas fa-file-pdf pdf-icon"></i></button>
        </div>
  
        <!-- Información general -->
        <div class="info-general">
          <p><strong>Número de Orden:</strong> {{ detalleOrden?.numero_orden || 'N/A' }}</p>
          <p><strong>Producto:</strong> {{ detalleOrden?.producto_compuesto_nombre || 'N/A' }}</p>
          <p><strong>Cantidad de Paquetes:</strong> {{ detalleOrden?.cantidad_paquetes || 'N/A' }}</p>
          <p><strong>Bodega de Producción:</strong> {{ detalleOrden?.bodega_produccion_nombre || 'No especificada' }}</p>
          <p><strong>Estado:</strong> {{ detalleOrden?.estado || 'N/A' }}</p>
        </div>
  
        <!-- Tabla de costos -->
        <table class="tabla-costos">
          <tbody>
            <tr>
              <td class="label">Costo Unitario</td>
              <td class="value">${{ detalleOrden?.costo_unitario?.toFixed(2) || 'N/A' }}</td>
              <td class="label">Costo Total</td>
              <td class="value">${{ detalleOrden?.costo_total?.toFixed(2) || 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
  
        <!-- Tabla de fechas -->
        <table class="tabla-fechas">
          <thead>
            <tr>
              <th colspan="4">-- Fechas de Producción --</th>
            </tr>
            <tr>
              <th>Creación</th>
              <th>Lista para Producción</th>
              <th>Inicia Producción</th>
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
        <table class="tabla-responsables">
          <tbody>
            <tr>
              <td class="label">Creado por</td>
              <td class="value">{{ detalleOrden?.creado_por || 'N/A' }}</td>
              <td class="label">Producido por</td>
              <td class="value">{{ detalleOrden?.en_produccion_por || 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
  
        <!-- Tabla de componentes -->
        <table class="tabla-componentes">
          <thead>
            <tr>
              <th style="width: 60%">Componente</th>
              <th style="width: 10%">Cant. x Paquete</th>
              <th style="width: 10%">Cant. Total</th>
              <th style="width: 10%">Peso x Paquete</th>
              <th style="width: 10%">Peso Total</th>
              <th style="width: 10%">Costo Unitario</th>
              <th style="width: 10%">Costo Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="componente in componentes" :key="componente.nombre">
              <td>{{ componente.nombre }}</td>
              <td>{{ componente.cant_x_paquete }}</td>
              <td>{{ componente.cantidad_total.toFixed(2) }}</td>
              <td>{{ componente.peso_x_paquete }}</td>
              <td>{{ componente.peso_total.toFixed(2) }}</td>
              <td>${{ componente.costo_unitario.toFixed(2) }}</td>
              <td>${{ componente.costo_total.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
  
      <!-- Opciones de Producción -->
      <section v-if="detalleOrden && (detalleOrden.estado === 'En Producción' || detalleOrden.estado === 'En Producción-Parcial' || detalleOrden.estado === 'Finalizada')">
        <h3>Opciones de Producción</h3>
        
        <div v-if="detalleOrden.estado === 'En Producción' || detalleOrden.estado === 'En Producción-Parcial'">
          <button @click="habilitarEntregaParcial" :disabled="cantidadPendiente === 0">
            Entrega Parcial
          </button>
          <button v-if="detalleOrden.estado === 'En Producción'" @click="realizarEntregaTotal">
            Entrega Total
          </button>
          <button v-if="detalleOrden.estado === 'En Producción-Parcial'" @click="habilitarCierreForzado">
            Cierre Forzado
          </button>
  
          <div v-if="cierreForzadoHabilitado">
            <textarea v-model="comentarioCierreForzado" placeholder="Ingrese un comentario (opcional)"></textarea>
            <button @click="confirmarCierreForzado">Confirmar Cierre</button>
          </div>
        </div>
  
        <div v-if="entregaParcialHabilitada">
          <label for="cantidad-parcial">Cantidad Parcial a Entregar:</label>
          <input type="number" v-model="cantidadParcial" min="1" :max="cantidadPendiente" />
          <label for="comentario">Comentario (opcional):</label>
          <input type="text" v-model="comentarioParcial" placeholder="Añadir un comentario..." />
          <button @click="registrarEntregaParcial">Entregar</button>
        </div>
  
        <h3>Historial de Entregas</h3>
        <table v-if="historialEntregas.length > 0">
          <thead>
            <tr>
              <th>Cantidad Entregada</th>
              <th>Fecha y Hora</th>
              <th>Comentario</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entrega in historialEntregas" :key="entrega.id">
              <td>{{ entrega.cantidad }}</td>
              <td>{{ formatFecha(entrega.fecha_hora) }}</td>
              <td>{{ entrega.comentario || 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>No hay entregas registradas para esta orden.</p>
  
        <p><strong>Cantidad Pendiente:</strong> {{ cantidadPendiente }}</p>
  
        <!-- Mostrar estado de la orden -->
        <div>
          <h3 v-if="detalleOrden.estado === 'Finalizada' && detalleOrden.comentario_cierre_forzado">
            Orden con Cierre Forzado
          </h3>
          <p v-if="detalleOrden.estado === 'Finalizada' && detalleOrden.comentario_cierre_forzado">
            {{ detalleOrden.comentario_cierre_forzado }}
          </p>
          <h3 v-else-if="detalleOrden.estado === 'Finalizada'">
            Orden Finalizada sin novedad
          </h3>
          <h3 v-else>
            Estado Actual: {{ detalleOrden.estado }}
          </h3>
        </div>
      </section>
    </div>
  </template>
  
  <script>
  import { ref } from 'vue';
  import { useStore } from 'vuex';
  import { useRouter } from 'vue-router';
  import axios from '@/api/axios';
  import * as XLSX from 'xlsx';
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
  
  export default {
    data() {
      return {
        productosCompuestos: [],
        bodegas: [],
        nuevaOrden: {
          producto_compuesto_id: null,
          cantidad_paquetes: null,
          bodega_produccion: null,
        },
        codigoProductoCompuesto: "",
        nombreProductoCompuesto: "",
        filtroEstado: "",
        filtroNumeroOrden: "",
        ordenes: [],
        tablaRevisarVisible: false,
        componentes: [],
        detalleOrden: {},
        tablaDetalleVisible: false,
        historialEntregas: [],
        cantidadParcial: 0,
        comentarioParcial: "",
        cantidadPendiente: 0,
        entregasTotales: 0,
        entregaParcialHabilitada: false,
        mostrarDetalle: false,
        cierreForzadoHabilitado: false,
        comentarioCierreForzado: "",
      };
    },
    methods: {
      formatFecha(fecha) {
        if (!fecha) return "-";
        const fechaObj = new Date(fecha);
        return fechaObj.toLocaleString("es-CO", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
      },
      limpiarPagina() {
        this.nuevaOrden = {
          producto_compuesto_id: null,
          cantidad_paquetes: null,
          bodega_produccion: null,
        };
        this.codigoProductoCompuesto = "";
        this.nombreProductoCompuesto = "";
        this.filtroEstado = "";
        this.filtroNumeroOrden = "";
        this.ordenes = [];
        this.tablaRevisarVisible = false;
        this.componentes = [];
        this.detalleOrden = {};
        this.tablaDetalleVisible = false;
        this.historialEntregas = [];
        this.cantidadParcial = 0;
        this.comentarioParcial = "";
        this.cantidadPendiente = 0;
        this.entregasTotales = 0;
        this.entregaParcialHabilitada = false;
        this.mostrarDetalle = false;
        this.cierreForzadoHabilitado = false;
        this.comentarioCierreForzado = "";
        this.cargarProductosCompuestos();
        this.cargarBodegas();
      },
      sincronizarPorNombre() {
        const productoEncontrado = this.productosCompuestos.find(p => 
          p.nombre.toLowerCase().includes(this.nombreProductoCompuesto.toLowerCase())
        );
        if (productoEncontrado) {
          this.nuevaOrden.producto_compuesto_id = productoEncontrado.id;
          this.codigoProductoCompuesto = productoEncontrado.codigo;
        }
      },
      sincronizarCodigoConSelector() {
        const productoEncontrado = this.productosCompuestos.find(p => p.codigo === this.codigoProductoCompuesto);
        if (productoEncontrado) {
          this.nuevaOrden.producto_compuesto_id = productoEncontrado.id;
          this.nombreProductoCompuesto = productoEncontrado.nombre;
        }
      },
      sincronizarSelectorConCodigo() {
        const productoSeleccionado = this.productosCompuestos.find(p => p.id === this.nuevaOrden.producto_compuesto_id);
        if (productoSeleccionado) {
          this.codigoProductoCompuesto = productoSeleccionado.codigo;
          this.nombreProductoCompuesto = productoSeleccionado.nombre;
        }
      },
      async cargarBodegas() {
        try {
          const response = await apiClient.get("/inventory/bodegas");
          this.bodegas = response.data;
        } catch (error) {
          console.error("Error al cargar las bodegas:", error);
          alert("No se pudieron cargar las bodegas.");
        }
      },
      async cargarProductosCompuestos() {
        try {
          const response = await apiClient.get("/inventory/productos-compuestos");
          this.productosCompuestos = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
        } catch (error) {
          console.error("Error al cargar productos compuestos:", error);
          alert("No se pudieron cargar los productos compuestos.");
        }
      },
      async consultarOrdenes() {
        try {
          let params = {};
          if (this.filtroEstado) {
            params.estado = this.filtroEstado;
          }
          if (this.filtroNumeroOrden) {
            params.numero_orden = this.filtroNumeroOrden;
          }
          const response = await apiClient.get("/api/ordenes-produccion", { params });
          this.ordenes = response.data.sort((a, b) => b.id - a.id);
          this.mostrarDetalle = false;
          this.detalleOrden = {};
        } catch (error) {
          console.error("Error al consultar órdenes de producción:", error);
          alert("No se pudieron consultar las órdenes de producción.");
        }
      },
      async revisarOrden() {
        try {
          if (!this.nuevaOrden.producto_compuesto_id || !this.nuevaOrden.cantidad_paquetes) {
            alert("Por favor, selecciona un producto y una cantidad válida.");
            return;
          }
          const response = await apiClient.get(
            `/inventory/productos-compuestos/detalle?id=${this.nuevaOrden.producto_compuesto_id}`
          );
          if (!response.data.materiales || !Array.isArray(response.data.materiales)) {
            throw new Error("La respuesta del backend no contiene materiales válidos.");
          }
          this.componentes = response.data.materiales.map((componente) => {
            const cantidad = Number(componente.cantidad);
            const pesoUnitario = Number(componente.peso_unitario);
            const cantidadPaquetes = Number(this.nuevaOrden.cantidad_paquetes);
            if (isNaN(cantidad) || isNaN(pesoUnitario) || isNaN(cantidadPaquetes)) {
              throw new Error(`Valores no numéricos detectados: cantidad=${componente.cantidad}, peso_unitario=${componente.peso_unitario}`);
            }
            return {
              nombre: componente.producto_base_nombre,
              cantidad_requerida: cantidad,
              cantidad_total: cantidad * cantidadPaquetes,
              peso_unitario: pesoUnitario,
              peso_total: cantidad * cantidadPaquetes * pesoUnitario,
              costo_unitario: componente.costo_unitario || 0,
              costo_total: (componente.costo_unitario || 0) * cantidad * cantidadPaquetes
            };
          });
          this.tablaRevisarVisible = true;
        } catch (error) {
          console.error("Error al revisar orden:", error);
          alert("No se pudo revisar la orden: " + (error.message || "Error desconocido"));
          this.tablaRevisarVisible = false;
        }
      },
      async crearOrden() {
        if (!Number.isInteger(this.nuevaOrden.cantidad_paquetes) || this.nuevaOrden.cantidad_paquetes < 1) {
          alert("La cantidad de paquetes debe ser un número entero positivo.");
          return;
        }
        try {
          const usuarioLogueado = localStorage.getItem("usuario_id");
          const response = await apiClient.post("/api/ordenes-produccion", {
            producto_compuesto_id: this.nuevaOrden.producto_compuesto_id,
            cantidad_paquetes: this.nuevaOrden.cantidad_paquetes,
            bodega_produccion: this.nuevaOrden.bodega_produccion,
            creado_por: usuarioLogueado,
          });
          alert(response.data.message);
          this.nuevaOrden = {
            producto_compuesto_id: null,
            cantidad_paquetes: null,
            bodega_produccion: null,
          };
          this.tablaRevisarVisible = false;
          this.componentes = [];
          await this.consultarOrdenes();
        } catch (error) {
          console.error("Error al crear orden de producción:", error);
          alert("No se pudo crear la orden de producción.");
        }
      },
      async eliminarOrden(ordenId) {
        try {
          const confirmacion = confirm("¿Estás seguro de que deseas eliminar esta orden?");
          if (!confirmacion) {
            return;
          }
          const response = await apiClient.delete(`/api/ordenes-produccion/${ordenId}`);
          alert(response.data.message);
          this.ordenes = this.ordenes.filter(orden => orden.id !== ordenId);
          if (this.detalleOrden.id === ordenId) {
            this.detalleOrden = {};
            this.tablaDetalleVisible = false;
          }
        } catch (error) {
          console.error("Error al eliminar la orden:", error);
          alert("No se pudo eliminar la orden.");
        }
      },
      async cargarDetalleOrden(ordenId) {
        try {
          const detalleResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}`);
          this.detalleOrden = {
            ...detalleResponse.data,
            bodega_produccion_nombre: detalleResponse.data.bodega_produccion_nombre || "No especificada",
            costo_unitario: detalleResponse.data.costo_unitario || 0,
            costo_total: detalleResponse.data.costo_total || 0,
            comentario_cierre_forzado: detalleResponse.data.comentario_cierre_forzado || ""
          };
          const materialesResponse = await apiClient.get(`/inventory/productos-compuestos/detalle?id=${this.detalleOrden.producto_compuesto_id}`);
          this.componentes = materialesResponse.data.materiales.map((componente) => ({
            nombre: componente.producto_base_nombre,
            cant_x_paquete: componente.cantidad,
            peso_x_paquete: componente.peso_unitario,
            cantidad_total: componente.cantidad * this.detalleOrden.cantidad_paquetes,
            peso_total: componente.cantidad * this.detalleOrden.cantidad_paquetes * componente.peso_unitario,
            costo_unitario: componente.costo_unitario || 0,
            costo_total: (componente.costo_unitario || 0) * componente.cantidad * this.detalleOrden.cantidad_paquetes
          }));
          const historialResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}/historial-entregas`);
          this.historialEntregas = historialResponse.data.historial || [];
          this.entregasTotales = historialResponse.data.total_entregado || 0;
          this.cantidadPendiente = historialResponse.data.cantidad_pendiente || this.detalleOrden.cantidad_paquetes;
          this.tablaDetalleVisible = true;
        } catch (error) {
          console.error("Error al cargar detalle de la orden:", error);
          alert("No se pudo cargar el detalle de la orden.");
          this.tablaDetalleVisible = false;
        }
      },
      async actualizarEstado(ordenId, nuevoEstado) { 
        try {
          const usuarioId = localStorage.getItem("usuario_id");
          if (!usuarioId) {
            alert("No se pudo obtener el ID del usuario logueado.");
            return;
          }
          const response = await apiClient.put(`/api/ordenes-produccion/${ordenId}/estado`, {
            nuevo_estado: nuevoEstado,
            usuario_id: usuarioId,
          });
          alert(response.data.message);
          await this.consultarOrdenes();
          if (this.detalleOrden.id === ordenId) {
            await this.cargarDetalleOrden(ordenId);
          }
        } catch (error) {
          console.error("Error al actualizar el estado de la orden:", error);
          alert("No se pudo actualizar el estado de la orden.");
        }
      },
      habilitarEntregaParcial() {
        this.entregaParcialHabilitada = true;
      },
      habilitarCierreForzado() {
        this.cierreForzadoHabilitado = true;
      },
      async registrarEntregaParcial() {
        if (!this.cantidadParcial || this.cantidadParcial <= 0 || this.cantidadParcial > this.cantidadPendiente) {
          alert("Por favor, ingrese una cantidad válida menor o igual a la cantidad pendiente.");
          return;
        }
        try {
          const usuarioId = localStorage.getItem("usuario_id");
          if (!usuarioId) {
            alert("No se pudo obtener el ID del usuario logueado.");
            return;
          }
          const response = await apiClient.post(`/api/ordenes-produccion/${this.detalleOrden.id}/entrega-parcial`, {
            cantidad_entregada: this.cantidadParcial,
            comentario: this.comentarioParcial,
            usuario_id: usuarioId,
          });
          alert(response.data.message);
          this.entregaParcialHabilitada = false;
          this.cantidadParcial = 0;
          this.comentarioParcial = "";
          await this.cargarDetalleOrden(this.detalleOrden.id);
          await this.consultarOrdenes();
        } catch (error) {
          console.error("Error al registrar entrega parcial:", error);
          alert("No se pudo registrar la entrega parcial.");
        }
      },
      async realizarEntregaTotal() {
        try {
          if (!this.detalleOrden || !this.detalleOrden.id) {
            alert("No se puede finalizar la orden porque no se encontró el detalle.");
            return;
          }
          const confirmacion = confirm("¿Estás seguro de registrar la entrega total?");
          if (!confirmacion) return;
          const response = await apiClient.post(`/api/ordenes-produccion/${this.detalleOrden.id}/registrar-entrega-total`);
          alert(response.data.message);
          await this.cargarDetalleOrden(this.detalleOrden.id);
          await this.consultarOrdenes();
        } catch (error) {
          console.error("Error al registrar entrega total:", error);
          alert("No se pudo registrar la entrega total.");
        }
      },
      async registrarProduccion(ordenId) {
        try {
          if (!this.detalleOrden || this.detalleOrden.id !== ordenId) {
            await this.cargarDetalleOrden(ordenId);
          }
          if (this.detalleOrden.estado === 'En Producción' || this.detalleOrden.estado === 'En Producción-Parcial') {
            this.mostrarDetalle = true;
          } else {
            alert("La orden no está en estado válido para registrar producción.");
          }
        } catch (error) {
          console.error("Error al registrar producción:", error);
          alert("No se pudo mostrar las opciones de producción.");
        }
      },
      async confirmarCierreForzado() {
        try {
          if (!this.detalleOrden || !this.detalleOrden.id) {
            alert("No se puede cerrar la orden porque no se encontró el detalle.");
            return;
          }
          const confirmacion = confirm(`¿Seguro que deseas cerrar forzadamente la orden ${this.detalleOrden.numero_orden}?`);
          if (!confirmacion) return;
          const response = await apiClient.post(`/api/ordenes-produccion/${this.detalleOrden.id}/cierre-forzado`, {
            comentario: this.comentarioCierreForzado
          });
          alert(response.data.message);
          this.cierreForzadoHabilitado = false;
          this.comentarioCierreForzado = "";
          await this.cargarDetalleOrden(this.detalleOrden.id);
          await this.consultarOrdenes();
        } catch (error) {
          console.error("Error al realizar el Cierre Forzado:", error);
          alert("No se pudo completar el Cierre Forzado.");
        }
      },
      async descargarPdf(ordenId) {
        try {
          const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf`, {
            responseType: "blob",
          });
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", `Orden_${ordenId}.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (error) {
          console.error("Error al descargar el PDF:", error);
          alert("No se pudo descargar el PDF de la orden.");
        }
      },
      async descargarPdfOperador(ordenId) {
        try {
          const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf-operador`, {
            responseType: "blob",
          });
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", `Orden_${ordenId}_Operador.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (error) {
          console.error("Error al descargar el PDF para operador:", error);
          alert("No se pudo descargar el PDF de la orden.");
        }
      },
      volverAlMenu() {
        const tipoUsuario = localStorage.getItem("tipo_usuario");
        if (tipoUsuario === "admin") {
          this.$router.push('/menu');
        } else if (tipoUsuario === "gerente") {
          this.$router.push('/menu-gerente');
        } else {
          alert("Rol no reconocido. Contacta al administrador.");
        }
      },
    },
    mounted() {
      this.cargarProductosCompuestos();
      this.cargarBodegas();
    },
  };
  
  </script>
  
<style scoped>
.produccion-admin {
  margin: 20px auto;
  max-width: 1200px;
  font-family: Arial, sans-serif;
  padding: 10px;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 20px;
}

h2, h3 {
  color: #34495e;
  margin-bottom: 15px;
}

button {
  padding: 0.6rem 1.2rem;
  border: none;
  background-color: #42b983;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  margin-right: 10px;
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

button.btn-danger {
  background-color: #dc3545;
}

button.btn-danger:hover {
  background-color: #c82333;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

form label {
  font-weight: bold;
  display: block;
  margin-bottom: 5px;
  color: #555;
}

form input, form select {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  font-size: 14px;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background-color: #f8f9fa;
  color: #333;
  font-weight: bold;
}

tbody tr:nth-child(odd) {
  background-color: #f9f9f9;
}

tbody tr:hover {
  background-color: #f1f1f1;
}

section {
  margin-bottom: 30px;
  padding: 15px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background-color: #f8f9fa;
}

p {
  margin: 5px 0;
  color: #555;
  font-size: 14px;
}

.detalle-orden {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.acciones-orden {
  margin-bottom: 15px;
}

.info-general p {
  margin: 5px 0;
  font-size: 14px;
  color: #333;
}

.info-general p strong {
  color: #0056b3;
}

.tabla-costos {
  width: 100%;
  margin: 15px 0;
  border-collapse: collapse;
  background-color: #f8f9fa;
  border-radius: 4px;
  overflow: hidden;
}

.tabla-costos td {
  padding: 10px;
  border: 1px solid #e9ecef;
  text-align: center;
}

.tabla-costos .label {
  background-color: #e9ecef;
  font-weight: bold;
  color: #555;
}

.tabla-costos .value {
  color: #007bff;
  font-weight: bold;
}

.tabla-fechas {
  width: 100%;
  margin: 15px 0;
  border-collapse: collapse;
  background-color: #f8f9fa;
  border-radius: 4px;
  overflow: hidden;
}

.tabla-fechas th, .tabla-fechas td {
  padding: 10px;
  border: 1px solid #e9ecef;
  text-align: center;
  width: 25%;
  height: 40px;
}

.tabla-fechas th {
  background-color: #e9ecef;
  color: #555;
  font-weight: bold;
}

.tabla-fechas td {
  color: #333;
  font-size: 12px;
}

.tabla-responsables {
  width: 100%;
  margin: 15px 0;
  border-collapse: collapse;
  background-color: #f8f9fa;
  border-radius: 4px;
  overflow: hidden;
}

.tabla-responsables td {
  padding: 10px;
  border: 1px solid #e9ecef;
  text-align: center;
}

.tabla-responsables .label {
  background-color: #e9ecef;
  font-weight: bold;
  color: #555;
}

.tabla-responsables .value {
  color: #333;
}

.tabla-componentes {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  font-size: 14px;
  background-color: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.tabla-componentes th, .tabla-componentes td {
  border: 1px solid #e9ecef;
  padding: 10px;
  text-align: left;
}

.tabla-componentes th {
  background-color: #f8f9fa;
  color: #333;
  font-weight: bold;
}

.tabla-componentes tbody tr:nth-child(odd) {
  background-color: #f9f9f9;
}

.tabla-componentes tbody tr:hover {
  background-color: #f1f1f1;
}

@media (max-width: 768px) {
  .produccion-admin {
    margin: 10px auto;
    padding: 10px;
  }

  form input, form select, button {
    width: 100%;
    margin-bottom: 10px;
    font-size: 16px;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  th, td {
    font-size: 12px;
    padding: 8px;
  }

  h1 {
    font-size: 20px;
  }

  h2, h3 {
    font-size: 18px;
  }

  .detalle-orden {
    padding: 15px;
  }

  .tabla-costos, .tabla-fechas, .tabla-responsables, .tabla-componentes {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    font-size: 12px;
  }

  .tabla-costos td, .tabla-fechas th, .tabla-fechas td, .tabla-responsables td {
    padding: 8px;
  }

  .tabla-fechas td {
    font-size: 10px;
  }
}
</style>