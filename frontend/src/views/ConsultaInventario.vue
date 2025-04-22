<template>
  <div class="consulta-inventario">
    <h1>Consulta de Inventario</h1>

    <section class="form-section">
      <div class="form-actions" style="justify-content: flex-end">
          <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
          
      </div>

      <!-- Filtros de búsqueda -->
      <div class="form-group">
        <label for="nombreFiltro">Buscar por nombre:</label>
        <input
          type="text"
          id="nombreFiltro"
          v-model="nombreDigitado"
          placeholder="Ingrese nombre del producto"
          @input="sincronizarPorNombre"
        />
      </div>
      <div class="form-group">
        <label for="codigoFiltro">Buscar por código:</label>
        <input
          v-model="codigoDigitado"
          id="codigoFiltro"
          placeholder="Ingrese código de producto"
          @input="sincronizarCodigoConSelector"
        />
      </div>
      <div class="form-group">
        <label for="productoSelector">Seleccione un producto:</label>
        <select v-model="filtroProducto" id="productoSelector" @change="sincronizarSelectorConCodigo">
          <option value="">Todos</option>
          <option v-for="producto in productosDisponibles" :key="producto.codigo" :value="producto.codigo">
            {{ producto.codigo }} - {{ producto.nombre }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="filtroEstado">Filtrar por Estado:</label>
        <select v-model="filtroEstado" id="filtroEstado" @change="consultar">
          <option value="">Todos</option>
          <option value="verde">Verde (OK)</option>
          <option value="amarillo">Amarillo (Advertencia)</option>
          <option value="rojo">Rojo (Crítico)</option>
        </select>
      </div>
      <div class="form-actions">
        <button @click="consultar" class="btn">Consultar Inventario</button>
      </div>
    </section>

    <!-- Filtros adicionales para consulta general -->
    <section v-if="mostrarInventario && filtroProducto === '' && codigoDigitado === '' && nombreDigitado === ''" class="form-section">
      <div class="form-group">
        <label for="filtroBodega">Filtrar por bodega:</label>
        <select v-model="filtroBodega" id="filtroBodega" @change="filtrarPorBodega">
          <option value="">Todas</option>
          <option v-for="bodega in bodegas" :key="bodega" :value="bodega">{{ bodega }}</option>
        </select>
      </div>
      <div class="form-group">
        <label for="umbralAlerta">Umbral de Alerta (%):</label>
        <input v-model.number="umbralAlerta" id="umbralAlerta" type="number" min="0" max="100" step="1" />
      </div>
    </section>

    <!-- Resumen de Costos -->
    <section v-if="mostrarInventario && filtroProducto === '' && codigoDigitado === '' && nombreDigitado === ''" class="form-section">
      <h2>Resumen de Costos por Almacén</h2>
      <div class="table-container">
        <table class="resumen-costos">
          <thead>
            <tr>
              <th>Almacén</th>
              <th>Costo Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(costo, bodega) in resumenCostos" :key="bodega">
              <td>{{ bodega }}</td>
              <td>${{ formatCosto(costo) }}</td>
            </tr>
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>${{ formatCosto(Object.values(resumenCostos).reduce((sum, costo) => sum + costo, 0)) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Tabla de Inventario -->
    <section v-if="mostrarInventario">
      <h2>Inventario de Productos</h2>
      <div class="form-actions">
        <button v-if="productosFiltrados.length" @click="exportarAExcel" class="btn">
          Exportar a Excel <font-awesome-icon icon="file-excel" class="excel-icon" />
        </button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Stock Mínimo</th>
              <th>Total</th>
              <th>Estado</th>
              <template v-for="bodega in bodegasMostradas" :key="bodega">
                <th>{{ bodega }}</th>
                <th>Costo Total {{ bodega }}</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr v-for="producto in productosFiltrados" :key="producto.codigo">
              <td>{{ producto.codigo }}</td>
              <td>{{ producto.nombre }}</td>
              <td>{{ producto.stock_minimo !== null ? producto.stock_minimo : '-' }}</td>
              <td>{{ producto.cantidad_total || 0 }}</td>
              <td>
                <span v-if="producto.stock_minimo !== null && producto.stock_minimo !== undefined">
                  <span v-if="Number(producto.cantidad_total) > Number(producto.stock_minimo) * (1 + Number(umbralAlerta) / 100)" class="estado verde">✔</span>
                  <span v-else-if="Number(producto.cantidad_total) > Number(producto.stock_minimo)" class="estado amarillo">⚠</span>
                  <span v-else class="estado rojo">✖</span>
                </span>
                <span v-else>-</span>
              </td>
              <template v-for="bodega in bodegasMostradas" :key="bodega">
                <td>{{ producto.cantidades_por_bodega[bodega] || 0 }}</td>
                <td>${{ formatCosto(producto.costos_por_bodega[bodega] || 0) }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="filtroProducto === '' && codigoDigitado === '' && nombreDigitado === ''" class="paginacion">
        <button :disabled="paginaActual === 1" @click="cambiarPagina(paginaActual - 1)" class="btn">Anterior</button>
        <span>Página {{ paginaActual }}</span>
        <button :disabled="productosFiltrados.length < limite" @click="cambiarPagina(paginaActual + 1)" class="btn">Siguiente</button>
      </div>
    </section>
  </div>
</template>

<script>
import apiClient from '@/api/axios';
import * as XLSX from "xlsx";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

export default {
  name: "ConsultaInventario",
  components: { FontAwesomeIcon },
  data() {
    return {
      filtroProducto: "",
      codigoDigitado: "",
      nombreDigitado: "",
      productosDisponibles: [],
      productos: [],
      productosFiltrados: [],
      bodegas: [],
      bodegasMostradas: [],
      filtroBodega: "",
      filtroEstado: "",
      mostrarInventario: false,
      paginaActual: 1,
      limite: 20,
      todosLosProductos: [],
      umbralAlerta: 10,
    };
  },
  computed: {
    resumenCostos() {
      const resumen = {};
      this.bodegas.forEach((bodega) => {
        resumen[bodega] = this.todosLosProductos.reduce((total, producto) => {
          return total + (producto.costos_por_bodega[bodega] || 0);
        }, 0);
      });
      return resumen;
    },
  },
  methods: {
    limpiarPagina() {
      this.codigoDigitado = "";
      this.nombreDigitado = "";
      this.filtroProducto = "";
      this.filtroBodega = "";
      this.filtroEstado = "";
      this.productos = [];
      this.productosFiltrados = [];
      this.bodegas = [];
      this.bodegasMostradas = [];
      this.mostrarInventario = false;
      this.paginaActual = 1;
      this.todosLosProductos = [];
      this.umbralAlerta = 10;
    },
    async consultar() {
      if (this.filtroProducto || this.codigoDigitado || this.nombreDigitado) {
        await this.consultarProductoEspecifico();
        if (this.filtroEstado) {
          this.filtrarPorEstado();
        }
      } else {
        await this.consultarTodosLosProductos();
        if (this.filtroEstado) {
          this.filtrarPorEstado();
        }
      }
    },
    async consultarProductoEspecifico() {
      try {
        const codigo = this.filtroProducto || this.codigoDigitado;
        let url = "";
        if (codigo) {
          url = `/api/inventario-con-costos/${codigo}`;
        } else if (this.nombreDigitado) {
          url = `/api/inventario-con-costos?nombre=${encodeURIComponent(this.nombreDigitado)}&limit=999999`;
        } else {
          alert('Por favor, ingrese un código o nombre de producto.');
          this.mostrarInventario = false;
          this.productos = [];
          this.bodegas = [];
          this.productosFiltrados = [];
          return;
        }

        const response = await apiClient.get(url);
        const data = response.data;

        if (data.message) {
          alert(data.message);
          this.mostrarInventario = false;
          this.productos = [];
          this.bodegas = [];
          this.productosFiltrados = [];
          return;
        }

        const bodegasResponse = await apiClient.get("/inventory/bodegas");
        const todasLasBodegas = bodegasResponse.data.map((b) => b.nombre);

        this.bodegas = todasLasBodegas;
        this.bodegasMostradas = todasLasBodegas;

        if (data.producto) {
          const inventario = data.inventario || [];
          this.productos = [
            {
              codigo: data.producto.codigo,
              nombre: data.producto.nombre,
              cantidad_total: inventario.reduce((total, item) => {
                const cantidad = Number(item.cantidad) || 0;
                return total + cantidad;
              }, 0),
              stock_minimo: data.producto.stock_minimo !== null ? Number(data.producto.stock_minimo) : null,
              cantidades_por_bodega: todasLasBodegas.reduce((acc, bodega) => {
                const item = inventario.find((i) => i.bodega === bodega);
                acc[bodega] = item ? Number(item.cantidad) || 0 : 0;
                return acc;
              }, {}),
              costos_por_bodega: todasLasBodegas.reduce((acc, bodega) => {
                const item = inventario.find((i) => i.bodega === bodega);
                acc[bodega] = item ? Number(item.costo_total) || 0 : 0;
                return acc;
              }, {})
            }
          ];
        } else if (data.productos) {
          this.productos = data.productos
            .sort((a, b) => a.codigo.localeCompare(b.codigo))
            .map((producto) => ({
              codigo: producto.codigo,
              nombre: producto.nombre,
              cantidad_total: Number(producto.cantidad_total) || 0,
              stock_minimo: producto.stock_minimo !== null ? Number(producto.stock_minimo) : null,
              cantidades_por_bodega: { ...producto.cantidades_por_bodega },
              costos_por_bodega: { ...producto.costos_por_bodega }
            }));
        } else {
          alert('No se encontraron datos para el producto especificado.');
          this.productos = [];
          this.productosFiltrados = [];
          this.mostrarInventario = false;
          return;
        }

        this.productosFiltrados = [...this.productos];
        this.mostrarInventario = true;
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;
        alert(`Error al consultar el inventario: ${errorMsg}`);
        this.mostrarInventario = false;
        this.productos = [];
        this.productosFiltrados = [];
      }
    },
    async consultarTodosLosProductos() {
      try {
        const fullResponse = await apiClient.get("/api/inventario-con-costos?limit=999999");
        const { productos, bodegas } = fullResponse.data;

        if (!productos || productos.length === 0) {
          alert("No se encontró información en el inventario.");
          this.mostrarInventario = false;
          this.bodegas = [];
          this.productos = [];
          this.productosFiltrados = [];
          this.todosLosProductos = [];
          return;
        }

        this.bodegas = bodegas || [];
        this.bodegasMostradas = [...this.bodegas];

        this.todosLosProductos = productos
          .sort((a, b) => a.codigo.localeCompare(b.codigo))
          .map((producto) => ({
            codigo: producto.codigo,
            nombre: producto.nombre,
            cantidad_total: Number(producto.cantidad_total) || 0,
            stock_minimo: producto.stock_minimo !== null ? Number(producto.stock_minimo) : null,
            cantidades_por_bodega: { ...producto.cantidades_por_bodega },
            costos_por_bodega: { ...producto.costos_por_bodega }
          }));

        const offset = (this.paginaActual - 1) * this.limite;
        this.productos = this.todosLosProductos.slice(offset, offset + this.limite);
        this.productosFiltrados = [...this.productos];
        this.mostrarInventario = true;
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;
        alert(`Error al consultar el inventario general: ${errorMsg}`);
      }
    },
    filtrarPorBodega() {
      if (this.filtroBodega) {
        this.bodegasMostradas = [this.filtroBodega];
        this.productosFiltrados = this.todosLosProductos
          .filter((producto) => (producto.cantidades_por_bodega[this.filtroBodega] || 0) > 0)
          .slice((this.paginaActual - 1) * this.limite, this.paginaActual * this.limite);
      } else {
        this.bodegasMostradas = [...this.bodegas];
        this.productosFiltrados = this.todosLosProductos.slice(
          (this.paginaActual - 1) * this.limite,
          this.paginaActual * this.limite
        );
      }
    },
    filtrarPorEstado() {
      if (!this.filtroEstado) {
        if (this.filtroProducto || this.codigoDigitado || this.nombreDigitado) {
          return;
        }
        this.productosFiltrados = this.todosLosProductos.slice(
          (this.paginaActual - 1) * this.limite,
          this.paginaActual * this.limite
        );
      } else {
        const source = (this.filtroProducto || this.codigoDigitado || this.nombreDigitado)
          ? this.productos
          : this.todosLosProductos;
        this.productosFiltrados = source.filter((producto) => {
          if (producto.stock_minimo === null || producto.stock_minimo === undefined) {
            return false;
          }
          const umbral = Math.ceil(Number(producto.stock_minimo) * (Number(this.umbralAlerta) / 100));
          const diff = Number(producto.cantidad_total) - Number(producto.stock_minimo);
          if (this.filtroEstado === "verde") return diff > umbral;
          if (this.filtroEstado === "amarillo") return diff <= umbral && diff > 0;
          if (this.filtroEstado === "rojo") return diff <= 0;
          return false;
        });
        if (!(this.filtroProducto || this.codigoDigitado || this.nombreDigitado)) {
          this.productosFiltrados = this.productosFiltrados.slice(
            (this.paginaActual - 1) * this.limite,
            this.paginaActual * this.limite
          );
        }
      }
    },
    async cargarProductosDisponibles() {
      try {
        const response = await apiClient.get("/api/productos/completos");
        this.productosDisponibles = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;
        alert(`Error al cargar productos disponibles: ${errorMsg}`);
      }
    },
    cambiarPagina(nuevaPagina) {
      this.paginaActual = nuevaPagina;
      const offset = (this.paginaActual - 1) * this.limite;
      this.productos = this.todosLosProductos.slice(offset, offset + this.limite);
      this.productosFiltrados = [...this.productos];
    },
    sincronizarPorNombre() {
      if (!this.nombreDigitado) {
        this.filtroProducto = "";
        this.codigoDigitado = "";
        return;
      }
      const productoEncontrado = this.productosDisponibles.find((p) =>
        p.nombre.toLowerCase().includes(this.nombreDigitado.toLowerCase())
      );
      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.codigoDigitado = productoEncontrado.codigo;
      }
    },
    sincronizarCodigoConSelector() {
      if (!this.codigoDigitado) {
        this.filtroProducto = "";
        this.nombreDigitado = "";
        return;
      }
      const productoEncontrado = this.productosDisponibles.find((p) =>
        p.codigo.toLowerCase() === this.codigoDigitado.toLowerCase()
      );
      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.nombreDigitado = productoEncontrado.nombre;
      }
    },
    sincronizarSelectorConCodigo() {
      if (!this.filtroProducto) {
        this.codigoDigitado = "";
        this.nombreDigitado = "";
        return;
      }
      const productoSeleccionado = this.productosDisponibles.find((p) => p.codigo === this.filtroProducto);
      if (productoSeleccionado) {
        this.codigoDigitado = productoSeleccionado.codigo;
        this.nombreDigitado = productoSeleccionado.nombre;
      }
    },
    formatCosto(costo) {
      return Number(costo).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    exportarAExcel() {
      const dataToExport = this.filtroProducto || this.codigoDigitado || this.nombreDigitado
        ? this.productosFiltrados
        : this.todosLosProductos;

      let worksheetData = [];

      if (!this.filtroProducto && !this.codigoDigitado && !this.nombreDigitado) {
        worksheetData = [
          ["Resumen de Costos por Almacén"],
          ["Almacén", "Costo Total"],
          ...Object.entries(this.resumenCostos).map(([bodega, costo]) => [bodega, costo]),
          ["TOTAL", Object.values(this.resumenCostos).reduce((sum, costo) => sum + costo, 0)],
          [""]
        ];
      }

      const getEstado = (producto) => {
        if (producto.stock_minimo === null || producto.stock_minimo === undefined) {
          return "-";
        }
        const cantidadTotal = Number(producto.cantidad_total);
        const stockMinimo = Number(producto.stock_minimo);
        const umbral = Math.ceil(stockMinimo * (Number(this.umbralAlerta) / 100));
        if (cantidadTotal > stockMinimo + umbral) {
          return "✔";
        } else if (cantidadTotal > stockMinimo) {
          return "⚠";
        } else {
          return "✖";
        }
      };

      worksheetData.push(
        ["Inventario de Productos"],
        ["Código", "Nombre", "Stock Mínimo", "Total", "Estado", ...this.bodegas.flatMap((bodega) => [bodega, `Costo Total ${bodega}`])],
        ...dataToExport.map((producto) => [
          producto.codigo,
          producto.nombre,
          producto.stock_minimo !== null ? producto.stock_minimo : "-",
          producto.cantidad_total,
          getEstado(producto),
          ...this.bodegas.flatMap((bodega) => [
            producto.cantidades_por_bodega[bodega] || 0,
            producto.costos_por_bodega[bodega] || 0
          ])
        ])
      );

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Inventario");
      XLSX.writeFile(workbook, `inventario_${new Date().toISOString().slice(0, 10)}.xlsx`);
    }
  },
  mounted() {
    this.cargarProductosDisponibles();
  }
};
</script>

<style scoped>
.consulta-inventario {
  padding: 20px;
  max-width: 1200px;
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

.form-section {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
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
  text-align: left;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
  color: #34495e;
}

tbody tr:nth-child(odd) {
  background-color: #f9f9f9;
}

tbody tr:hover {
  background-color: #f1f1f1;
}

.resumen-costos {
  width: 50%;
  margin: 0 auto;
}

.resumen-costos th,
.resumen-costos td {
  padding: 12px;
  text-align: center;
}

.total-row {
  font-weight: bold;
  background-color: #e9ecef;
}

.estado.verde {
  color: green;
  font-size: 18px;
}

.estado.amarillo {
  color: #ffc107;
  font-size: 18px;
}

.estado.rojo {
  color: red;
  font-size: 18px;
}

.excel-icon {
  margin-left: 5px;
}

.paginacion {
  margin-top: 20px;
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.paginacion button {
  padding: 8px 16px;
}

@media (max-width: 768px) {
  .form-group input,
  .form-group select {
    font-size: 16px;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  .resumen-costos {
    width: 100%;
  }
}
</style>

