<template>
    <div class="consulta-inventario">
      <h1>Consulta de Inventario de Productos</h1>
  
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
        <div class="form-actions">
            <button @click="consultar" class="btn">Consultar Inventario</button>
        </div>
      </section>
  
      <!-- Filtro por Bodega -->
      <section v-if="mostrarInventario && filtroProducto === '' && codigoDigitado === ''" class="form-section">
        <div class="form-group">
          <label for="filtroBodega">Filtrar por bodega:</label>
          <select v-model="filtroBodega" id="filtroBodega" @change="filtrarPorBodega">
            <option value="">Todas</option>
            <option v-for="bodega in bodegas" :key="bodega" :value="bodega">{{ bodega }}</option>
          </select>
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
                <th>Total</th>
                <th v-for="bodega in bodegasMostradas" :key="bodega">{{ bodega }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="producto in productosFiltrados" :key="producto.codigo">
                <td>{{ producto.codigo }}</td>
                <td>{{ producto.nombre }}</td>
                <td>{{ producto.cantidad_total }}</td>
                <td v-for="bodega in bodegasMostradas" :key="bodega">
                  {{ producto.cantidades_por_bodega[bodega] || 0 }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="filtroProducto === '' && codigoDigitado === ''" class="paginacion">
          <button :disabled="paginaActual === 1" @click="cambiarPagina(paginaActual - 1)" class="btn">Anterior</button>
          <span>Página {{ paginaActual }}</span>
          <button :disabled="productos.length < limite" @click="cambiarPagina(paginaActual + 1)" class="btn">Siguiente</button>
        </div>
      </section>
    </div>
  </template>
  
  <script>
  import apiClient from '@/api/axios';
  import * as XLSX from "xlsx";
  
  export default {
    name: "ConsultaInventarioLite",
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
        mostrarInventario: false,
        paginaActual: 1,
        limite: 20,
        todosLosProductos: [],
      };
    },
    methods: {
      limpiarPagina() {
        this.codigoDigitado = "";
        this.nombreDigitado = "";
        this.filtroProducto = "";
        this.filtroBodega = "";
        this.productos = [];
        this.productosFiltrados = [];
        this.bodegas = [];
        this.bodegasMostradas = [];
        this.mostrarInventario = false;
        this.paginaActual = 1;
        this.todosLosProductos = [];
      },
      async consultar() {
        if (this.filtroProducto || this.codigoDigitado || this.nombreDigitado) {
          await this.consultarProductoEspecifico();
        } else {
          await this.consultarTodosLosProductos();
        }
      },
      async consultarProductoEspecifico() {
        try {
          const codigo = this.filtroProducto || this.codigoDigitado;
          let url = `/api/inventario/${codigo}`;
          if (this.nombreDigitado && !codigo) {
            url = `/api/inventario?nombre=${encodeURIComponent(this.nombreDigitado)}&limit=999999`;
          }
          const response = await apiClient.get(url);
          const data = response.data;
  
          if (data.error) {
            alert(data.error);
            this.limpiarPagina();
            return;
          }
          if (data.message) {
            alert(data.message);
            this.mostrarInventario = false;
            this.productos = [];
            this.bodegas = [];
            return;
          }
  
          const bodegasResponse = await apiClient.get("/inventory/bodegas");
          const todasLasBodegas = bodegasResponse.data.map((b) => b.nombre);
  
          this.bodegas = todasLasBodegas;
          this.bodegasMostradas = todasLasBodegas;
          if (data.producto) {
            this.productos = [{
              codigo: data.producto.codigo,
              nombre: data.producto.nombre,
              cantidad_total: data.inventario.reduce((total, item) => total + item.cantidad, 0),
              cantidades_por_bodega: todasLasBodegas.reduce((acc, bodega) => {
                const item = data.inventario.find((i) => i.bodega === bodega);
                acc[bodega] = item ? item.cantidad : 0;
                return acc;
              }, {}),
            }];
          } else {
            this.productos = data.productos.map(producto => ({
              codigo: producto.codigo,
              nombre: producto.nombre,
              cantidad_total: producto.cantidad_total,
              cantidades_por_bodega: producto.cantidades_por_bodega,
            }));
          }
          this.productosFiltrados = [...this.productos];
          this.mostrarInventario = true;
        } catch (error) {
          console.error("Error al consultar inventario específico:", error);
          if (error.response?.status === 403) {
            alert("No tienes permiso para consultar el inventario.");
            this.$router.push('/login');
          } else if (error.response?.status === 404) {
            alert("Producto no encontrado.");
          } else {
            alert("Ocurrió un error al consultar el inventario.");
          }
          this.mostrarInventario = false;
        }
      },
      async consultarTodosLosProductos() {
        try {
          const offset = (this.paginaActual - 1) * this.limite;
          const response = await apiClient.get(`/api/inventario?offset=${offset}&limit=${this.limite}`);
          const { productos, bodegas, total } = response.data;
  
          if (!productos || productos.length === 0) {
            alert("No se encontró información en el inventario.");
            this.mostrarInventario = false;
            return;
          }
  
          this.bodegas = bodegas || [];
          this.bodegasMostradas = [...this.bodegas];
          this.productos = productos.map((producto) => ({
            codigo: producto.codigo,
            nombre: producto.nombre,
            cantidad_total: producto.cantidad_total,
            cantidades_por_bodega: { ...producto.cantidades_por_bodega },
          }));
          this.productosFiltrados = [...this.productos];
          this.mostrarInventario = true;
  
          if (total > this.limite) {
            const fullResponse = await apiClient.get("/api/inventario?limit=999999");
            this.todosLosProductos = fullResponse.data.productos.map((producto) => ({
              codigo: producto.codigo,
              nombre: producto.nombre,
              cantidad_total: producto.cantidad_total,
              cantidades_por_bodega: { ...producto.cantidades_por_bodega },
            }));
          } else {
            this.todosLosProductos = [...this.productos];
          }
        } catch (error) {
          console.error("Error al consultar inventario general:", error);
          if (error.response?.status === 403) {
            alert("No tienes permiso para consultar el inventario.");
            this.$router.push('/login');
          } else {
            alert("Ocurrió un error al consultar el inventario general.");
          }
          this.mostrarInventario = false;
        }
      },
      filtrarPorBodega() {
        if (this.filtroBodega) {
          this.bodegasMostradas = [this.filtroBodega];
          this.productosFiltrados = this.productos.map(producto => ({
            ...producto,
            cantidad_total: producto.cantidades_por_bodega[this.filtroBodega] || 0,
          }));
        } else {
          this.bodegasMostradas = [...this.bodegas];
          this.productosFiltrados = [...this.productos];
        }
      },
      async cargarProductosDisponibles() {
        try {
          const response = await apiClient.get("/api/productos/completos");
          this.productosDisponibles = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
        } catch (error) {
          console.error("Error al cargar productos disponibles:", error);
          if (error.response?.status === 403) {
            alert("No tienes permiso para acceder a los productos.");
            this.$router.push('/login');
          }
        }
      },
      cambiarPagina(nuevaPagina) {
        this.paginaActual = nuevaPagina;
        this.consultarTodosLosProductos();
      },
      sincronizarPorNombre() {
        const productoEncontrado = this.productosDisponibles.find(p => 
          p.nombre.toLowerCase().includes(this.nombreDigitado.toLowerCase())
        );
        if (productoEncontrado) {
          this.filtroProducto = productoEncontrado.codigo;
          this.codigoDigitado = productoEncontrado.codigo;
        }
      },
      sincronizarCodigoConSelector() {
        const productoEncontrado = this.productosDisponibles.find(p => p.codigo === this.codigoDigitado);
        if (productoEncontrado) {
          this.filtroProducto = productoEncontrado.codigo;
          this.nombreDigitado = productoEncontrado.nombre;
        }
      },
      sincronizarSelectorConCodigo() {
        const productoSeleccionado = this.productosDisponibles.find(p => p.codigo === this.filtroProducto);
        if (productoSeleccionado) {
          this.codigoDigitado = productoSeleccionado.codigo;
          this.nombreDigitado = productoSeleccionado.nombre;
        } else {
          this.codigoDigitado = "";
          this.nombreDigitado = "";
        }
      },
      volverAlMenu() {
        this.$router.push('/menu-operador');
      },
      exportarAExcel() {
        const dataToExport = this.filtroProducto || this.codigoDigitado || this.nombreDigitado 
          ? this.productosFiltrados 
          : this.todosLosProductos;
  
        const worksheetData = [
          ["Consulta de Inventario de Productos"],
          ["Código", "Nombre", "Total", ...this.bodegasMostradas],
          ...dataToExport.map(producto => [
            producto.codigo,
            producto.nombre,
            producto.cantidad_total,
            ...this.bodegasMostradas.map(bodega => producto.cantidades_por_bodega[bodega] || 0),
          ]),
        ];
  
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Inventario");
        XLSX.writeFile(workbook, `inventario_${new Date().toISOString().slice(0,10)}.xlsx`);
      },
    },
    mounted() {
      this.cargarProductosDisponibles();
    },
  }
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
  }
  </style>