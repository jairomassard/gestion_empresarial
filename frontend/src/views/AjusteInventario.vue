<template>
  <div class="ajuste-inventario">
    <h1>Ajuste Manual de Inventario</h1>

    <!-- Botones de Navegación -->
    <div class="top-buttons">
      
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Realizar Ajuste Manual -->
    <section class="form-section">
      <h2>Realizar Ajuste Manual de Inventario</h2>
      <div class="form-grid">
        <!-- Fila 1: Búsqueda por nombre y código -->
        <div class="filter-group">
          <label for="nombreFiltro">Buscar por nombre:</label>
          <input
            v-model="nombreDigitado"
            id="nombreFiltro"
            placeholder="Ingrese nombre del producto"
            @input="sincronizarPorNombre"
          />
        </div>
        <div class="filter-group">
          <label for="codigoFiltro">Buscar por código:</label>
          <input
            v-model="codigoDigitado"
            id="codigoFiltro"
            placeholder="Ingrese código del producto"
            @input="sincronizarCodigoConSelector"
          />
        </div>
        <!-- Fila 2: Select y botón -->
        <div class="filter-group">
          <label for="productoSelector">Seleccione un producto:</label>
          <select v-model="filtroProducto" id="productoSelector" @change="sincronizarSelectorConCodigo">
            <option value="" disabled>Seleccione un producto</option>
            <option v-for="producto in productosDisponibles" :key="producto.id" :value="producto.codigo">
              {{ producto.codigo }} - {{ producto.nombre }}
            </option>
          </select>
        </div>
        <div class="filter-actions">
          <button @click="consultar" class="btn">Consultar Inventario</button>
        </div>
      </div>

      <!-- Tabla de Inventario -->
      <div v-if="mostrarInventario" class="card-container">
        <h3>Inventario Disponible</h3>
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Total</th>
              <th v-for="bodega in bodegas" :key="bodega.id">{{ bodega.nombre }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="producto in productos" :key="producto.codigo">
              <td>{{ producto.codigo }}</td>
              <td>{{ producto.nombre }}</td>
              <td>{{ producto.cantidad_total }}</td>
              <td v-for="bodega in bodegas" :key="bodega.id">
                {{ producto.cantidades_por_bodega[bodega.nombre] || 0 }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Formulario de Ajuste -->
      <div v-if="mostrarInventario" class="form-section">
        <h3>Ajuste de Inventario</h3>
        <!-- Fila 1: Bodega y Acción -->
        <div class="filter-group">
          <label for="bodegaSelector">Seleccione la bodega:</label>
          <select v-model="bodegaSeleccionada" id="bodegaSelector">
            <option value="" disabled>Seleccione una bodega</option>
            <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
              {{ bodega.nombre }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label for="accionSelector">Acción:</label>
          <select v-model="accionSeleccionada" id="accionSelector">
            <option value="Incrementar">Incrementar</option>
            <option value="Disminuir">Disminuir</option>
          </select>
        </div>
        <!-- Fila 2: Cantidad y Botón -->
        <div class="filter-group">
          <label for="cantidadAjuste">Cantidad:</label>
          <input v-model.number="cantidadAjuste" id="cantidadAjuste" type="number" min="1" />
        </div>
        <div class="filter-actions">
          <button @click="agregarProductoAjuste" class="btn">Agregar Producto</button>
        </div>
      </div>
    </section>

    <!-- Productos a Ajustar -->
    <section v-if="productosEnAjuste.length" class="form-section">
      <h2>Productos a Ajustar</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Bodega</th>
              <th>Acción</th>
              <th>Cantidad</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(producto, index) in productosEnAjuste" :key="index">
              <td>{{ producto.codigo }}</td>
              <td>{{ producto.nombre }}</td>
              <td>{{ producto.bodega }}</td>
              <td>{{ producto.accion }}</td>
              <td>{{ producto.cantidad }}</td>
              <td>
                <button @click="eliminarProductoAjuste(index)" class="btn btn-danger">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="form-actions">
        <button @click="realizarAjuste" class="btn">Realizar Ajuste</button>
      </div>
    </section>

    <!-- Consulta de Ajustes -->
    <section class="form-section">
      <h2>Consulta de Ajustes de Inventario</h2>
      <div class="form-grid">
        <!-- Fila 1: Transacción -->
        <div class="filter-group">
          <label for="filtroTransaccion">Número de Transacción:</label>
          <input
            v-model="filtroTransaccion"
            id="filtroTransaccion"
            placeholder="Ingrese número de transacción"
          />
        </div>
        <!-- Fila 2: Fechas -->
        <div class="dates-grid">
          <div class="filter-group">
            <label for="fechaInicio">Fecha Inicio:</label>
            <input type="date" v-model="fechaInicio" id="fechaInicio" />
          </div>
          <div class="filter-group">
            <label for="fechaFin">Fecha Fin:</label>
            <input type="date" v-model="fechaFin" id="fechaFin" />
          </div>
        </div>
        <!-- Nota -->
        <div class="filter-group full-width">
          <p class="info-message">
            Nota: Para incluir movimientos del día actual, seleccione un día adicional como fecha final.
          </p>
        </div>
        <!-- Botón -->
        <div class="filter-actions">
          <button @click="consultarAjustes" class="btn">Buscar Ajustes</button>
        </div>
      </div>

      <!-- Resultados de Ajustes -->
      <section v-if="ajustes.length" class="card-container">
        <h3>Resultados de Ajustes</h3>
        <div class="form-actions">
          <button @click="imprimirAjustes_listadoPDF" class="btn btn-export">
            Imprimir Listado <font-awesome-icon icon="file-pdf" class="pdf-icon" />
          </button>
          <button @click="exportarAjustes_listadoExcel" class="btn btn-export">
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
            <tr v-for="ajuste in ajustes" :key="ajuste.consecutivo">
              <td>{{ ajuste.consecutivo }}</td>
              <td>{{ ajuste.fecha }}</td>
              <td>
                <button @click="verDetalle(ajuste.consecutivo)" class="btn">Detalle</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Detalle del Ajuste -->
      <section v-if="detalleAjuste.length" class="card-container">
        <h3>Detalle del Ajuste {{ ajusteSeleccionado }}</h3>
        <div class="form-actions">
          <button @click="imprimirAjustePDF" class="btn btn-export">
            Imprimir <font-awesome-icon icon="file-pdf" class="pdf-icon" />
          </button>
          <button @click="exportarAjusteExcel" class="btn btn-export">
            Exportar <font-awesome-icon icon="file-excel" class="excel-icon" />
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre Producto</th>
              <th>Bodega</th>
              <th>Cantidad Anterior</th>
              <th>Acción</th>
              <th>Cantidad Ajustada</th>
              <th>Cantidad Final</th>
              <th>Costo Unitario</th>
              <th>Costo Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="detalle in detalleAjuste" :key="detalle.id">
              <td>{{ detalle.codigo_producto }}</td>
              <td>{{ detalle.nombre_producto }}</td>
              <td>{{ detalle.bodega_nombre }}</td>
              <td>{{ detalle.cantidad_anterior }}</td>
              <td>{{ detalle.tipo_movimiento }}</td>
              <td>{{ detalle.cantidad_ajustada }}</td>
              <td>{{ detalle.cantidad_final }}</td>
              <td>{{ detalle.costo_unitario ? `$${detalle.costo_unitario.toFixed(2)}` : 'N/A' }}</td>
              <td>{{ detalle.costo_total ? `$${detalle.costo_total.toFixed(2)}` : 'N/A' }}</td>
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
import { ref } from "vue";

export default {
  name: "AjusteInventario",
  setup() {
    // Estado para consulta de inventario
    const nombreDigitado = ref("");
    const codigoDigitado = ref("");
    const filtroProducto = ref("");
    const productosDisponibles = ref([]);
    const productos = ref([]);
    const bodegas = ref([]);
    const mostrarInventario = ref(false);

    // Estado para ajuste
    const bodegaSeleccionada = ref("");
    const accionSeleccionada = ref("Incrementar");
    const cantidadAjuste = ref(1);
    const productosEnAjuste = ref([]);

    // Estado para consulta de ajustes
    const filtroTransaccion = ref("");
    const fechaInicio = ref("");
    const fechaFin = ref("");
    const ajustes = ref([]);
    const detalleAjuste = ref([]);
    const ajusteSeleccionado = ref("");
    const fechaAjuste = ref("");

    // Cargar datos iniciales
    const cargarProductosDisponibles = async () => {
      try {
        const response = await apiClient.get("/api/productos/completos");
        productosDisponibles.value = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
      } catch (error) {
        console.error("Error al cargar productos disponibles:", error);
        alert("Error al cargar productos disponibles");
      }
    };

    // Consultar inventario
    const consultar = async () => {
      try {
        const codigo = codigoDigitado.value || filtroProducto.value;
        if (!codigo) {
          alert("Seleccione o escriba un producto para consultar.");
          return;
        }

        console.log("Consultando inventario para código:", codigo);
        const response = await apiClient.get(`/api/inventario/${codigo}`);
        const { producto, inventario } = response.data;
        const bodegasResponse = await apiClient.get("/inventory/bodegas");
        bodegas.value = bodegasResponse.data;

        productos.value = [
          {
            codigo: producto.codigo,
            nombre: producto.nombre,
            cantidad_total: inventario.reduce((total, item) => total + item.cantidad, 0),
            cantidades_por_bodega: Object.fromEntries(
              inventario.map((i) => [i.bodega, i.cantidad])
            ),
          },
        ];
        mostrarInventario.value = true;
      } catch (error) {
        console.error("Error al consultar inventario:", error);
        alert("Error al consultar inventario");
      }
    };

    // Sincronización
    const sincronizarPorNombre = () => {
      const productoEncontrado = productosDisponibles.value.find((p) =>
        p.nombre.toLowerCase().includes(nombreDigitado.value.toLowerCase())
      );
      if (productoEncontrado) {
        filtroProducto.value = productoEncontrado.codigo;
        codigoDigitado.value = productoEncontrado.codigo;
      }
    };

    const sincronizarCodigoConSelector = () => {
      const productoEncontrado = productosDisponibles.value.find(
        (p) => p.codigo === codigoDigitado.value
      );
      if (productoEncontrado) {
        filtroProducto.value = productoEncontrado.codigo;
        nombreDigitado.value = productoEncontrado.nombre;
      }
    };

    const sincronizarSelectorConCodigo = () => {
      const productoSeleccionado = productosDisponibles.value.find(
        (p) => p.codigo === filtroProducto.value
      );
      if (productoSeleccionado) {
        codigoDigitado.value = productoSeleccionado.codigo;
        nombreDigitado.value = productoSeleccionado.nombre;
      }
    };

    // Agregar producto a ajuste
    const agregarProductoAjuste = () => {
      const codigoSeleccionado = codigoDigitado.value.trim() || filtroProducto.value;
      if (
        !codigoSeleccionado ||
        !bodegaSeleccionada.value ||
        !accionSeleccionada.value ||
        !cantidadAjuste.value
      ) {
        alert("Seleccione un producto, bodega, tipo de movimiento y cantidad válida.");
        return;
      }

      const producto = productosDisponibles.value.find((p) => p.codigo === codigoSeleccionado);
      if (!producto) {
        alert("Producto no encontrado.");
        return;
      }

      productosEnAjuste.value.push({
        codigo: producto.codigo,
        nombre: producto.nombre,
        bodega: bodegaSeleccionada.value,
        accion: accionSeleccionada.value,
        cantidad: cantidadAjuste.value,
      });

      filtroProducto.value = "";
      codigoDigitado.value = "";
      nombreDigitado.value = "";
      accionSeleccionada.value = "Incrementar";
      cantidadAjuste.value = 1;
    };

    // Eliminar producto de ajuste
    const eliminarProductoAjuste = (index) => {
      productosEnAjuste.value.splice(index, 1);
    };

    // Realizar ajuste
    const realizarAjuste = async () => {
      try {
        if (!bodegaSeleccionada.value) {
          console.log("Validación fallida: No se seleccionó bodega");
          alert("Seleccione una bodega para realizar el ajuste.");
          return;
        }
        if (productosEnAjuste.value.length === 0) {
          console.log("Validación fallida: No hay productos para ajustar");
          alert("Agregue al menos un producto para ajustar.");
          return;
        }

        const productosParaAjuste = productosEnAjuste.value.map((producto) => ({
          codigoProducto: producto.codigo,
          tipoMovimiento: producto.accion,
          nuevaCantidad: producto.cantidad,
        }));

        console.log("Enviando solicitud de ajuste:", {
          bodega: bodegaSeleccionada.value,
          productos: productosParaAjuste,
        });

        const response = await apiClient.post("/api/ajuste-inventario", {
          bodega: bodegaSeleccionada.value,
          productos: productosParaAjuste,
        });

        console.log("Respuesta del ajuste:", response.data);
        alert(`Ajuste realizado con éxito. Consecutivo: ${response.data.consecutivo}`);

        const codigoProductoConsultado = filtroProducto.value || codigoDigitado.value;
        productosEnAjuste.value = [];
        filtroProducto.value = "";
        codigoDigitado.value = "";
        nombreDigitado.value = "";
        bodegaSeleccionada.value = "";
        accionSeleccionada.value = "Incrementar";
        cantidadAjuste.value = 1;
        mostrarInventario.value = false;

        if (codigoProductoConsultado) {
          await consultar();
        }
      } catch (error) {
        console.error("Error al realizar el ajuste:", error.response?.data || error.message);
        alert("Error al realizar el ajuste: " + (error.response?.data?.error || "Desconocido"));
      }
    };

    // Consultar ajustes
    const consultarAjustes = async () => {
      try {
        if (!filtroTransaccion.value && (!fechaInicio.value || !fechaFin.value)) {
          alert("Ingrese un número de transacción o un rango de fechas.");
          return;
        }

        const params = {};
        if (filtroTransaccion.value) params.consecutivo = filtroTransaccion.value;
        if (fechaInicio.value && fechaFin.value) {
          params.fechaInicio = fechaInicio.value;
          params.fechaFin = fechaFin.value;
        }

        console.log("Consultando ajustes con parámetros:", params);
        const response = await apiClient.get("/api/consulta-ajustes", { params });
        ajustes.value = response.data;
      } catch (error) {
        console.error("Error al consultar ajustes:", error);
        alert("Error al consultar ajustes");
      }
    };

    // Ver detalle de ajuste
    const verDetalle = async (consecutivo) => {
      try {
        ajusteSeleccionado.value = consecutivo;
        console.log("Consultando detalle para consecutivo:", consecutivo);
        const detalleResponse = await apiClient.get(`/api/ajuste-detalle/${consecutivo}`);
        detalleAjuste.value = detalleResponse.data;

        const consultaResponse = await apiClient.get("/api/consulta-ajustes", {
          params: { consecutivo },
        });
        const ajuste = consultaResponse.data.find((a) => a.consecutivo === consecutivo);
        fechaAjuste.value = ajuste ? ajuste.fecha : "Desconocida";
      } catch (error) {
        console.error("Error al obtener detalles del ajuste:", error);
        alert("Error al obtener detalles del ajuste");
      }
    };

    // Exportar e imprimir
    const imprimirAjustes_listadoPDF = async () => {
      try {
        if (!fechaInicio.value || !fechaFin.value) {
          alert("Especifique un rango de fechas para imprimir.");
          return;
        }

        console.log("Generando PDF de ajustes para fechas:", fechaInicio.value, fechaFin.value);
        const response = await apiClient.get("/api/consultaListado-ajustes-pdf", {
          params: {
            fechaInicio: fechaInicio.value,
            fechaFin: fechaFin.value,
          },
          responseType: "blob",
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute(
          "download",
          `ajustes_${fechaInicio.value}_al_${fechaFin.value}.pdf`
        );
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error("Error al generar el PDF de ajustes:", error);
        alert("Error al generar el PDF de ajustes");
      }
    };

    const imprimirAjustePDF = async () => {
      try {
        console.log("Generando PDF para ajuste:", ajusteSeleccionado.value);
        const response = await apiClient.get(
          `/api/ajuste-detalle-pdf/${ajusteSeleccionado.value}`,
          { responseType: "blob" }
        );

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `ajuste_${ajusteSeleccionado.value}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error("Error al generar el PDF del ajuste:", error);
        alert("Error al generar el PDF del ajuste");
      }
    };

    const exportarAjustes_listadoExcel = () => {
      if (!ajustes.value.length) {
        alert("No hay datos para exportar a Excel.");
        return;
      }
      if (!fechaInicio.value || !fechaFin.value) {
        alert("Especifique un rango de fechas para exportar.");
        return;
      }

      console.log("Exportando ajustes a Excel para fechas:", fechaInicio.value, fechaFin.value);
      const worksheetData = [
        ["Ajustes de Inventario Realizados"],
        [`Rango de fecha: ${fechaInicio.value} - ${fechaFin.value}`],
        [],
        ["Consecutivo", "Fecha"],
      ];

      ajustes.value.forEach((ajuste) => {
        worksheetData.push([ajuste.consecutivo, ajuste.fecha]);
      });

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Ajustes");
      XLSX.writeFile(
        workbook,
        `Listado_ajustes_${fechaInicio.value}_al_${fechaFin.value}.xlsx`
      );
    };

    const exportarAjusteExcel = () => {
      if (!detalleAjuste.value.length) {
        alert("No hay datos para exportar a Excel.");
        return;
      }

      console.log("Exportando detalle de ajuste a Excel para consecutivo:", ajusteSeleccionado.value);
      const nombres = localStorage.getItem("nombres") || "Desconocido";
      const apellidos = localStorage.getItem("apellidos") || "";
      const usuario = `${nombres} ${apellidos}`.trim();
      const fechaAjusteVal = fechaAjuste.value || "Desconocida";

      const worksheetData = [
        ["Ajuste de Inventario"],
        [`Detalle del Ajuste ${ajusteSeleccionado.value}`],
        [`Fecha Realización: ${fechaAjusteVal}`],
        [`Realizado por: ${usuario}`],
        [],
        [
          "Código",
          "Nombre Producto",
          "Bodega",
          "Cantidad Anterior",
          "Acción",
          "Cantidad Ajustada",
          "Cantidad Final",
          "Costo Unitario",
          "Costo Total",
        ],
      ];

      detalleAjuste.value.forEach((detalle) => {
        worksheetData.push([
          detalle.codigo_producto,
          detalle.nombre_producto,
          detalle.bodega_nombre,
          detalle.cantidad_anterior,
          detalle.tipo_movimiento,
          detalle.cantidad_ajustada,
          detalle.cantidad_final,
          detalle.costo_unitario ? detalle.costo_unitario.toFixed(2) : "N/A",
          detalle.costo_total ? detalle.costo_total.toFixed(2) : "N/A",
        ]);
      });

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Ajuste");
      XLSX.writeFile(workbook, `ajuste_${ajusteSeleccionado.value}.xlsx`);
    };

    // Limpiar página
    const limpiarPagina = () => {
      console.log("Limpiando página");
      codigoDigitado.value = "";
      nombreDigitado.value = "";
      filtroProducto.value = "";
      mostrarInventario.value = false;
      bodegaSeleccionada.value = "";
      accionSeleccionada.value = "Incrementar";
      cantidadAjuste.value = 1;
      productosEnAjuste.value = [];
      filtroTransaccion.value = "";
      fechaInicio.value = "";
      fechaFin.value = "";
      ajustes.value = [];
      detalleAjuste.value = [];
      ajusteSeleccionado.value = "";
      cargarProductosDisponibles();
    };

    // Volver al menú
    const volverAlMenu = () => {
      console.log("Volviendo al menú principal");
      const tipoUsuario = localStorage.getItem("tipo_usuario");
      const rutas = {
        admin: "/menu",
        gerente: "/menu-gerente",
        operador: "/menu-operador",
      };
      router.push(rutas[tipoUsuario] || "/");
    };

    // Cargar datos al montar
    cargarProductosDisponibles();

    return {
      nombreDigitado,
      codigoDigitado,
      filtroProducto,
      productosDisponibles,
      productos,
      bodegas,
      mostrarInventario,
      bodegaSeleccionada,
      accionSeleccionada,
      cantidadAjuste,
      productosEnAjuste,
      filtroTransaccion,
      fechaInicio,
      fechaFin,
      ajustes,
      detalleAjuste,
      ajusteSeleccionado,
      fechaAjuste,
      consultar,
      sincronizarPorNombre,
      sincronizarCodigoConSelector,
      sincronizarSelectorConCodigo,
      agregarProductoAjuste,
      eliminarProductoAjuste,
      realizarAjuste,
      consultarAjustes,
      verDetalle,
      imprimirAjustes_listadoPDF,
      imprimirAjustePDF,
      exportarAjustes_listadoExcel,
      exportarAjusteExcel,
      limpiarPagina,
      volverAlMenu,
    };
  },
};
</script>

<style scoped>
.ajuste-inventario {
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

.btn-secondary {
  background-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #5a6268;
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  flex-direction: column;
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

.dates-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  width: 100%;
}

.full-width {
  grid-column: 1 / -1;
}

.info-message {
  margin: 5px 0;
  color: #555;
  font-size: 14px;
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
  .form-grid {
    grid-template-columns: 1fr;
  }

  .dates-grid {
    grid-template-columns: 1fr;
  }

  .filter-group {
    min-width: 100%;
  }

  .table-container {
    display: block;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>