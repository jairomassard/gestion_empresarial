<template>
  <div class="trasladar-cantidades">
    <h1>Trasladar Cantidades entre Bodegas</h1>

    <!-- Botones de Navegación -->
    <div class="top-buttons">
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Consulta de Inventario -->
    <section class="form-section">
      <h2>Consulta de Inventario</h2>
      <h3>Buscar por:</h3>
      <div class="filters">
        <div class="filter-group">
          <label for="nombreConsulta">Nombre:</label>
          <input
            v-model="nombreConsulta"
            id="nombreConsulta"
            placeholder="Ingrese nombre del producto"
            @input="sincronizarPorNombre"
          />
        </div>
        <div class="filter-group">
          <label for="productoConsulta">Selección del producto:</label>
          <select v-model="productoConsulta" id="productoConsulta" @change="sincronizarSelectorConCodigo">
            <option value="" disabled>Seleccione un producto</option>
            <option v-for="producto in productos" :key="producto.id" :value="producto.codigo">
              {{ producto.codigo }} - {{ producto.nombre }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label for="codigoConsulta">Código del producto:</label>
          <input
            v-model="codigoConsulta"
            id="codigoConsulta"
            placeholder="Ingrese código del producto"
            @input="sincronizarCodigoConSelector"
          />
        </div>
        <div class="filter-actions">
          <button @click="consultarInventario" class="btn">Consultar Inventario</button>
        </div>
      </div>

      <div v-if="inventario.length" class="table-container">
        <h3>Inventario del Producto</h3>
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th v-for="bodega in bodegas" :key="bodega.id">{{ bodega.nombre }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ inventarioProducto.codigo }}</td>
              <td>{{ inventarioProducto.nombre }}</td>
              <td v-for="bodega in bodegas" :key="bodega.id">
                {{ obtenerCantidadEnBodega(bodega.nombre) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Agregar Productos al Traslado -->
    <section class="form-section">
      <h2>Agregar Productos al Traslado</h2>
      <h3>Buscar por:</h3>
      <div class="filters">
        <div class="filter-group">
          <label for="nombreTraslado">Nombre:</label>
          <input
            v-model="nombreTraslado"
            id="nombreTraslado"
            placeholder="Ingrese nombre del producto"
            @input="sincronizarPorNombreTraslado"
          />
        </div>
        <div class="filter-group">
          <label for="codigo">Selección del Producto:</label>
          <select v-model="nuevoTraslado.codigo" id="codigo" @change="sincronizarSelectorConCodigoTraslado">
            <option value="" disabled>Seleccione un producto</option>
            <option v-for="producto in productos" :key="producto.id" :value="producto.codigo">
              {{ producto.codigo }} - {{ producto.nombre }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label for="codigoIngresado">Código del producto:</label>
          <input
            v-model="codigoTraslado"
            id="codigoIngresado"
            placeholder="Ingrese código del producto"
            @input="sincronizarCodigoConSelectorTraslado"
          />
        </div>
        
        <!-- Agrupamos Bodega Origen y Destino en una fila -->
        <div class="bodegas-grid">
          <div class="filter-group">
            <label for="bodega_origen">Bodega Origen:</label>
            <select v-model="nuevoTraslado.bodega_origen" id="bodega_origen">
              <option value="" disabled>Seleccione una bodega</option>
              <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
                {{ bodega.nombre }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="bodega_destino">Bodega Destino:</label>
            <select v-model="nuevoTraslado.bodega_destino" id="bodega_destino">
              <option value="" disabled>Seleccione una bodega</option>
              <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
                {{ bodega.nombre }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="cantidad">Cantidad:</label>
            <input v-model.number="nuevoTraslado.cantidad" id="cantidad" type="number" min="1" />
          </div>
        </div>
        <div class="filter-actions">
          <button @click="agregarProductoATraslado" class="btn">Agregar Producto al Traslado</button>
        </div>
      </div>
    </section>

    <!-- Productos a Trasladar -->
    <section v-if="productosATrasladar.length" class="form-section">
      <h2>Productos en el Traslado</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Bodega Origen</th>
              <th>Bodega Destino</th>
              <th>Cantidad</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(producto, index) in productosATrasladar" :key="index">
              <td>{{ producto.codigo }}</td>
              <td>{{ producto.nombre }}</td>
              <td>{{ producto.bodega_origen }}</td>
              <td>{{ producto.bodega_destino }}</td>
              <td>{{ producto.cantidad }}</td>
              <td>
                <button @click="eliminarProductoDelTraslado(index)" class="btn btn-danger">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="form-actions">
        <button @click="confirmarTraslado" class="btn">Trasladar Productos</button>
      </div>
    </section>

    <!-- Consulta de Traslados -->
    <section class="form-section">
      <h2>Consulta de Traslados</h2>
      <h3>Buscar por:</h3>
      <div class="filters">
        <div class="filter-group">
          <label for="nombreConsultaTraslados">Nombre:</label>
          <input
            v-model="nombreConsultaTraslados"
            id="nombreConsultaTraslados"
            placeholder="Ingrese nombre del producto"
            @input="sincronizarPorNombreTraslados"
          />
        </div>
        <div class="filter-group">
          <label for="productoConsultaTraslados">Selección del Producto:</label>
          <select v-model="filtroProducto" id="productoConsultaTraslados" @change="sincronizarSelectorConCodigoTraslados">
            <option value="" disabled>Seleccione un producto</option>
            <option v-for="producto in productos" :key="producto.id" :value="producto.codigo">
              {{ producto.codigo }} - {{ producto.nombre }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label for="codigoConsultaTraslados">Código del producto:</label>
          <input
            v-model="codigoConsultaTraslados"
            id="codigoConsultaTraslados"
            placeholder="Ingrese código del producto"
            @input="sincronizarCodigoConSelectorTraslados"
          />
        </div>
        <div class="filter-group">
          <label for="consecutivo">Consecutivo:</label>
          <input v-model="filtroConsecutivo" id="consecutivo" placeholder="Ingrese consecutivo" />
        </div>
        <div class="fechas-grid">
          <div class="filter-group">
            <label for="fechaInicio">Fecha inicio:</label>
            <input type="date" id="fechaInicio" v-model="fechaInicio" />
          </div>
          <div class="filter-group">
            <label for="fechaFin">Fecha fin:</label>
            <input type="date" id="fechaFin" v-model="fechaFin" />
          </div>
          <div class="filter-group">
            <label for="filtroBodegaOrigen">Bodega de Origen:</label>
            <select v-model="filtroBodegaOrigen" id="filtroBodegaOrigen">
              <option value="" disabled>Seleccione una bodega</option>
              <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
                {{ bodega.nombre }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="filtroBodegaDestino">Bodega de Destino:</label>
            <select v-model="filtroBodegaDestino" id="filtroBodegaDestino">
              <option value="" disabled>Seleccione una bodega</option>
              <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
                {{ bodega.nombre }}
              </option>
            </select>
          </div>
          <div class="filter-actions">
            <button @click="consultarTraslados" class="btn">Consultar Traslados</button>
          </div>
        </div>
      </div>
      
      <section v-if="traslados.length" class="card-container">
        <h3>Resultados de la Consulta</h3>
        <div class="form-actions">
          <button @click="imprimirTrasladosPDF" class="btn btn-export">
            Imprimir Listado <font-awesome-icon icon="file-pdf" class="pdf-icon" />
          </button>
          <button @click="exportarTrasladosExcel" class="btn btn-export">
            Exportar Listado <font-awesome-icon icon="file-excel" class="excel-icon" />
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Consecutivo</th>
              <th>Fecha</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="traslado in traslados" :key="traslado.consecutivo">
              <td>{{ traslado.consecutivo }}</td>
              <td>{{ traslado.fecha }}</td>
              <td>
                <button @click="verDetalleTraslado(traslado.consecutivo)" class="btn">Detalle</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Detalle del Traslado -->
      <section v-if="detalleTraslado.length" class="card-container">
        <h3>Detalle del Traslado {{ trasladoSeleccionado }}</h3>
        <div class="form-actions">
          <button @click="imprimirDetalleTrasladoPDF" class="btn btn-export">
            Imprimir <font-awesome-icon icon="file-pdf" class="pdf-icon" />
          </button>
          <button @click="exportarDetalleTrasladoExcel" class="btn btn-export">
            Exportar <font-awesome-icon icon="file-excel" class="excel-icon" />
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Consecutivo</th>
              <th>Fecha</th>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Bodega Origen</th>
              <th>Bodega Destino</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in detalleTraslado" :key="item.id">
              <td>{{ item.consecutivo }}</td>
              <td>{{ item.fecha }}</td>
              <td>{{ item.producto }}</td>
              <td>{{ item.cantidad }}</td>
              <td>{{ item.bodega_origen }}</td>
              <td>{{ item.bodega_destino }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </section>
  </div>
</template>

<script>
import apiClient from '@/api/axios';
import * as XLSX from "xlsx";
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  name: "TrasladarCantidades",
  components: { FontAwesomeIcon },
  data() {
    return {
      productoConsulta: "",
      nombreConsulta: "",
      codigoConsulta: "",
      nuevoTraslado: {
        codigo: "",
        bodega_origen: "",
        bodega_destino: "",
        cantidad: 0,
      },
      nombreTraslado: "",
      codigoTraslado: "",
      productos: [],
      bodegas: [],
      productosATrasladar: [],
      inventario: [],
      inventarioProducto: {
        codigo: "",
        nombre: "",
      },
      filtroConsecutivo: "",
      filtroProducto: "",
      nombreConsultaTraslados: "",
      codigoConsultaTraslados: "",
      fechaInicio: "",
      fechaFin: "",
      filtroBodegaOrigen: "",
      filtroBodegaDestino: "",
      traslados: [],
      detalleTraslado: [],
      trasladoSeleccionado: "",
    };
  },
  methods: {
    limpiarPagina() {
      this.productoConsulta = "";
      this.nombreConsulta = "";
      this.codigoConsulta = "";
      this.inventario = [];
      this.inventarioProducto = { codigo: "", nombre: "" };
      this.nuevoTraslado = {
        codigo: "",
        bodega_origen: "",
        bodega_destino: "",
        cantidad: 0,
      };
      this.nombreTraslado = "";
      this.codigoTraslado = "";
      this.productosATrasladar = [];
      this.nombreConsultaTraslados = "";
      this.codigoConsultaTraslados = "";
      this.filtroConsecutivo = "";
      this.filtroProducto = "";
      this.fechaInicio = "";
      this.fechaFin = "";
      this.filtroBodegaOrigen = "";
      this.filtroBodegaDestino = "";
      this.traslados = [];
      this.detalleTraslado = [];
      this.trasladoSeleccionado = "";
    },
    async cargarProductos() {
      try {
        const response = await apiClient.get("/api/productos/completos");
        this.productos = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
      } catch (error) {
        console.error("Error al cargar productos:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para acceder a los productos.");
          this.$router.push('/login');
        } else {
          alert("No se pudieron cargar los productos.");
        }
      }
    },
    async cargarBodegas() {
      try {
        const response = await apiClient.get("/inventory/bodegas");
        this.bodegas = response.data;
      } catch (error) {
        console.error("Error al cargar bodegas:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para acceder a las bodegas.");
          this.$router.push('/login');
        } else {
          alert("No se pudieron cargar las bodegas.");
        }
      }
    },
    async consultarInventario() {
      if (!this.productoConsulta) {
        alert("Seleccione un producto para consultar su inventario");
        return;
      }
      try {
        const response = await apiClient.get(`/api/inventario/${this.productoConsulta}`);
        if (response.data.message) {
          alert(response.data.message);
          this.inventarioProducto = { codigo: "", nombre: "" };
          this.inventario = [];
          return;
        }
        this.inventarioProducto = response.data.producto;
        this.inventario = response.data.inventario;
      } catch (error) {
        console.error("Error al consultar inventario:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para consultar el inventario.");
          this.$router.push('/login');
        } else if (error.response?.status === 404) {
          alert("Producto no encontrado.");
        } else {
          alert("Ocurrió un error al consultar el inventario.");
        }
      }
    },
    obtenerCantidadEnBodega(nombreBodega) {
      const bodega = this.inventario.find((inv) => inv.bodega === nombreBodega);
      return bodega ? bodega.cantidad : 0;
    },
    async agregarProductoATraslado() {
      if (
        !this.nuevoTraslado.codigo ||
        !this.nuevoTraslado.bodega_origen ||
        !this.nuevoTraslado.bodega_destino ||
        !this.nuevoTraslado.cantidad ||
        this.nuevoTraslado.cantidad <= 0
      ) {
        alert("Complete todos los campos y asegúrese de que la cantidad sea mayor a 0.");
        return;
      }
      if (this.nuevoTraslado.bodega_origen === this.nuevoTraslado.bodega_destino) {
        alert("La bodega origen y destino no pueden ser la misma.");
        return;
      }
      const producto = this.productos.find((p) => p.codigo === this.nuevoTraslado.codigo);
      try {
        const response = await apiClient.get(`/api/inventario/${this.nuevoTraslado.codigo}`);
        const inventario = response.data.inventario;
        const cantidadEnOrigen = inventario.find(i => i.bodega === this.nuevoTraslado.bodega_origen)?.cantidad || 0;
        if (cantidadEnOrigen < this.nuevoTraslado.cantidad) {
          alert(`No hay suficiente inventario en ${this.nuevoTraslado.bodega_origen}. Disponible: ${cantidadEnOrigen}`);
          return;
        }
        this.productosATrasladar.push({
          ...this.nuevoTraslado,
          nombre: producto.nombre,
        });
        this.nuevoTraslado = { codigo: "", bodega_origen: "", bodega_destino: "", cantidad: 0 };
        this.nombreTraslado = "";
        this.codigoTraslado = "";
      } catch (error) {
        console.error("Error al verificar inventario:", error);
        alert("No se pudo verificar el inventario para el traslado.");
      }
    },
    eliminarProductoDelTraslado(index) {
      this.productosATrasladar.splice(index, 1);
    },
    async confirmarTraslado() {
      if (!this.productosATrasladar.length) {
          alert("Debe agregar al menos un producto al traslado.");
          return;
      }
      try {
          // Validar inventario nuevamente
          for (const producto of this.productosATrasladar) {
              const response = await apiClient.get(`/api/inventario/${producto.codigo}`);
              const inventario = response.data.inventario;
              const cantidadEnOrigen = inventario.find(i => i.bodega === producto.bodega_origen)?.cantidad || 0;
              console.debug(`Validando ${producto.codigo}: Disponible=${cantidadEnOrigen}, Requerido=${producto.cantidad}`);
              if (cantidadEnOrigen < producto.cantidad) {
                  alert(`Inventario insuficiente para ${producto.codigo} en ${producto.bodega_origen}. Disponible: ${cantidadEnOrigen}`);
                  return;
              }
          }

          const response = await apiClient.post("/api/trasladar_varios", {
              productos: this.productosATrasladar,
          });
          alert(`Traslado realizado con consecutivo: ${response.data.consecutivo}`);
          this.limpiarPagina();
      } catch (error) {
          console.error("Error al confirmar traslado:", error);
          if (error.response?.status === 403) {
              alert("No tienes permiso para realizar traslados.");
              this.$router.push('/login');
          } else if (error.response?.data?.error) {
              alert(error.response.data.error);
          } else {
              alert("Ocurrió un error al realizar el traslado.");
          }
      }
    },
    async consultarTraslados() {
      try {
        const params = {
          consecutivo: this.filtroConsecutivo || undefined,
          codigo: this.filtroProducto || undefined,
          fecha_inicio: this.fechaInicio || undefined,
          fecha_fin: this.fechaFin || undefined,
          bodega_origen: this.filtroBodegaOrigen || undefined,
          bodega_destino: this.filtroBodegaDestino || undefined,
        };
        const response = await apiClient.get("/api/traslados-por-bodega", { params });
        const uniqueTraslados = [];
        const seenConsecutivos = new Set();
        response.data.forEach(item => {
          if (!seenConsecutivos.has(item.consecutivo)) {
            seenConsecutivos.add(item.consecutivo);
            uniqueTraslados.push({
              consecutivo: item.consecutivo,
              fecha: item.fecha,
            });
          }
        });
        this.traslados = uniqueTraslados;
        this.detalleTraslado = [];
      } catch (error) {
        console.error("Error al consultar traslados:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para consultar traslados.");
          this.$router.push('/login');
        } else {
          alert("Ocurrió un error al consultar los traslados.");
        }
      }
    },
    async verDetalleTraslado(consecutivo) {
      try {
        this.trasladoSeleccionado = consecutivo;
        const response = await apiClient.get("/api/traslados", {
          params: { consecutivo },
        });
        this.detalleTraslado = response.data.map(item => ({
          id: `${item.consecutivo}-${item.producto}`,
          consecutivo: item.consecutivo,
          fecha: item.fecha,
          producto: item.producto,
          cantidad: item.cantidad,
          bodega_origen: item.bodega_origen,
          bodega_destino: item.bodega_destino,
        }));
      } catch (error) {
        console.error("Error al obtener detalle del traslado:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para ver detalles de traslados.");
          this.$router.push('/login');
        } else {
          alert("No se pudo recuperar el detalle del traslado.");
        }
      }
    },
    async imprimirTrasladosPDF() {
      try {
        const params = {
          consecutivo: this.filtroConsecutivo || undefined,
          codigo: this.filtroProducto || undefined,
          fecha_inicio: this.fechaInicio || undefined,
          fecha_fin: this.fechaFin || undefined,
          bodega_origen: this.filtroBodegaOrigen || undefined,
          bodega_destino: this.filtroBodegaDestino || undefined,
        };
        const response = await apiClient.get("/api/traslados-pdf", {
          params,
          responseType: "blob",
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `traslados_${this.fechaInicio || 'todos'}_al_${this.fechaFin || 'todos'}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error("Error al generar el PDF de traslados:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para generar PDFs.");
          this.$router.push('/login');
        } else {
          alert("No se pudo generar el PDF de traslados.");
        }
      }
    },
    exportarTrasladosExcel() {
      if (!this.traslados.length) {
        alert("No hay datos para exportar a Excel.");
        return;
      }
      const worksheetData = [
        ["Traslados Realizados"],
        [`Rango de fecha: ${this.fechaInicio || 'Todos'} - ${this.fechaFin || 'Todos'}`],
        [`Bodega de Origen: ${this.filtroBodegaOrigen || 'Cualquiera'}`],
        [`Bodega de Destino: ${this.filtroBodegaDestino || 'Cualquiera'}`],
        [],
        ["Consecutivo", "Fecha"],
      ];
      this.traslados.forEach((traslado) => {
        worksheetData.push([
          traslado.consecutivo,
          traslado.fecha,
        ]);
      });
      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Traslados");
      XLSX.writeFile(workbook, `traslados_${this.fechaInicio || 'todos'}_al_${this.fechaFin || 'todos'}.xlsx`);
    },
    async imprimirDetalleTrasladoPDF() {
      try {
        const response = await apiClient.get(`/api/traslado-detalle-pdf/${this.trasladoSeleccionado}`, {
          responseType: "blob",
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `traslado_${this.trasladoSeleccionado}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error("Error al generar el PDF del detalle del traslado:", error);
        if (error.response?.status === 403) {
          alert("No tienes permiso para generar PDFs.");
          this.$router.push('/login');
        } else {
          alert("No se pudo generar el PDF del detalle del traslado.");
        }
      }
    },
    exportarDetalleTrasladoExcel() {
      if (!this.detalleTraslado.length) {
        alert("No hay datos para exportar a Excel.");
        return;
      }
      const fechaTraslado = this.detalleTraslado[0].fecha;
      const worksheetData = [
        ["Traslado entre Bodegas"],
        [`Número Traslado: ${this.trasladoSeleccionado}`],
        [`Fecha del Traslado: ${fechaTraslado}`],
        [],
        ["Producto", "Cantidad", "Bodega Origen", "Bodega Destino"],
      ];
      this.detalleTraslado.forEach((item) => {
        worksheetData.push([
          item.producto,
          item.cantidad,
          item.bodega_origen,
          item.bodega_destino,
        ]);
      });
      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Detalle Traslado");
      XLSX.writeFile(workbook, `traslado_${this.trasladoSeleccionado}.xlsx`);
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
    sincronizarPorNombre() {
      const productoEncontrado = this.productos.find(p =>
        p.nombre.toLowerCase().includes(this.nombreConsulta.toLowerCase())
      );
      if (productoEncontrado) {
        this.productoConsulta = productoEncontrado.codigo;
        this.codigoConsulta = productoEncontrado.codigo;
      } else {
        this.productoConsulta = "";
        this.codigoConsulta = "";
      }
    },
    sincronizarCodigoConSelector() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.codigoConsulta);
      if (productoEncontrado) {
        this.productoConsulta = productoEncontrado.codigo;
        this.nombreConsulta = productoEncontrado.nombre;
      } else {
        this.productoConsulta = "";
        this.nombreConsulta = "";
      }
    },
    sincronizarSelectorConCodigo() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.productoConsulta);
      if (productoEncontrado) {
        this.codigoConsulta = productoEncontrado.codigo;
        this.nombreConsulta = productoEncontrado.nombre;
      } else {
        this.codigoConsulta = "";
        this.nombreConsulta = "";
      }
    },
    sincronizarPorNombreTraslado() {
      const productoEncontrado = this.productos.find(p =>
        p.nombre.toLowerCase().includes(this.nombreTraslado.toLowerCase())
      );
      if (productoEncontrado) {
        this.nuevoTraslado.codigo = productoEncontrado.codigo;
        this.codigoTraslado = productoEncontrado.codigo;
      } else {
        this.nuevoTraslado.codigo = "";
        this.codigoTraslado = "";
      }
    },
    sincronizarCodigoConSelectorTraslado() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.codigoTraslado);
      if (productoEncontrado) {
        this.nuevoTraslado.codigo = productoEncontrado.codigo;
        this.nombreTraslado = productoEncontrado.nombre;
      } else {
        this.nuevoTraslado.codigo = "";
        this.nombreTraslado = "";
      }
    },
    sincronizarSelectorConCodigoTraslado() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.nuevoTraslado.codigo);
      if (productoEncontrado) {
        this.nombreTraslado = productoEncontrado.nombre;
        this.codigoTraslado = productoEncontrado.codigo;
      } else {
        this.nombreTraslado = "";
        this.codigoTraslado = "";
      }
    },
    sincronizarPorNombreTraslados() {
      const productoEncontrado = this.productos.find(p =>
        p.nombre.toLowerCase().includes(this.nombreConsultaTraslados.toLowerCase())
      );
      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.codigoConsultaTraslados = productoEncontrado.codigo;
      } else {
        this.filtroProducto = "";
        this.codigoConsultaTraslados = "";
      }
    },
    sincronizarCodigoConSelectorTraslados() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.codigoConsultaTraslados);
      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.nombreConsultaTraslados = productoEncontrado.nombre;
      } else {
        this.filtroProducto = "";
        this.nombreConsultaTraslados = "";
      }
    },
    sincronizarSelectorConCodigoTraslados() {
      const productoEncontrado = this.productos.find(p => p.codigo === this.filtroProducto);
      if (productoEncontrado) {
        this.codigoConsultaTraslados = productoEncontrado.codigo;
        this.nombreConsultaTraslados = productoEncontrado.nombre;
      } else {
        this.codigoConsultaTraslados = "";
        this.nombreConsultaTraslados = "";
      }
    },
  },
  mounted() {
    this.cargarProductos();
    this.cargarBodegas();
  },
}
</script>

<style scoped>
.trasladar-cantidades {
  padding: 20px;
  max-width: 1400px;
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

h3 {
  font-size: 1.2rem;
  color: #34495e;
  margin-bottom: 10px;
}

.top-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  justify-content: flex-end;
}

button,
.btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

button:hover,
.btn:hover {
  background-color: #2c3e50;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-warning {
  background-color: #ffc107;
  color: #333;
}

.btn-warning:hover {
  background-color: #e0a800;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-export {
  background-color: #28a745;
}

.btn-export:hover {
  background-color: #218838;
}

.form-section {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 30px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  min-width: 200px;
  gap: 15px;
}

.filter-group label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;

}

.filter-group input,
.filter-group select {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.filter-actions {
  display: flex;
  gap: 15px;
  align-items: flex-end;
}

.bodegas-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr; /* tres columnas para Bodega Origen y Destino */
  gap: 15px;
  /*width: 100%; /* Ocupa el ancho disponible */
}
.fechas-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr; /* cinco columnas para Bodega Origen y Destino */
  gap: 15px;
  /*width: 100%; /* Ocupa el ancho disponible */
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

th,
td {
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

.pdf-icon,
.excel-icon {
  margin-left: 5px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }

  .bodegas-grid {
    grid-template-columns: 1fr; /* Apilar bodegas en móviles */
  }

  .table-container {
    display: block;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  .form-group input,
  .form-group select {
    font-size: 16px;
  }
}
</style>