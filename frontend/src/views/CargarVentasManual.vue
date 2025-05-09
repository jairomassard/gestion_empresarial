<template>
  <div class="cargar-ventas">
    <h1>Cargar Ventas Manualmente</h1>

    <section class="menu-buttons">
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </section>

    <!-- Mensaje de sincronización -->
    <section v-if="isSyncActive" class="form-section sync-warning">
      <h2>Advertencia</h2>
      <p>El cargue de ventas se debe hacer por la página de <strong>Cargar Ventas Diarias</strong> del módulo de Análisis debido a la sincronización activa parametrizada entre los módulos de Analisis e Inventarios.</p>
    </section>

    <!-- Subida de Archivo CSV -->
    <section class="form-section" v-if="!isSyncActive">
      <h2>Subir Archivo CSV</h2>
      <div class="form-group">
        <label for="inputCsv">Archivo CSV:</label>
        <input id="inputCsv" type="file" accept=".csv" @change="cargarCsv" ref="inputCsv" />
      </div>
      <button @click="procesarCsv" :disabled="isProcessing">Cargar Ventas</button>
    </section>

    <!-- Mostrar errores -->
    <section v-if="errores.length" class="form-section">
      <h2>Errores Detectados:</h2>
      <ul>
        <li v-for="(error, index) in errores" :key="index">{{ error }}</li>
      </ul>
    </section>

    <!-- Descarga de Plantilla -->
    <section class="form-section">
      <h2>Descargar Plantilla</h2>
      <button @click="descargarPlantilla">Descargar</button>
    </section>

    <!-- Consulta de Facturas de Venta -->
    <section class="consulta-ventas form-section">
      <h2>Consulta de Facturas de Venta</h2>
      <div class="form-group">
        <label for="filtroFactura">Número de Factura:</label>
        <input v-model="filtroFactura" id="filtroFactura" placeholder="Ingrese número de factura" />
      </div>
      <div class="form-group">
        <label for="fechaInicio">Fecha Inicio:</label>
        <input type="date" v-model="fechaInicio" id="fechaInicio" />
      </div>
      <div class="form-group">
        <label for="fechaFin">Fecha Fin:</label>
        <input type="date" v-model="fechaFin" id="fechaFin" />
      </div>
      <div class="form-group">
        <label for="filtroBodega">Bodega de Venta:</label>
        <select v-model="filtroBodega" id="filtroBodega">
          <option value="" disabled>Seleccione una bodega</option>
          <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.id">{{ bodega.nombre }}</option>
        </select>
      </div>
      <div class="form-group">
        <label for="selectorFactura">Seleccionar Factura:</label>
        <select v-model="filtroFactura" id="selectorFactura">
          <option value="" disabled>Seleccione una factura</option>
          <option v-for="factura in facturas" :key="factura" :value="factura">{{ factura }}</option>
        </select>
      </div>
      <button @click="consultarVentas">Consultar Facturas</button>
    </section>

    <!-- Resultados de la Consulta -->
    <section v-if="resultadosVentas.length" class="resultados-ventas form-section">
      <h3>Resultados de la Consulta</h3>
      <div class="form-actions">
        <button @click="exportarListadoExcel">Exportar Listado <font-awesome-icon icon="file-excel" class="excel-icon" /></button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Número de Factura</th>
              <th>Fecha y Hora</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="venta in resultadosVentas" :key="venta.factura">
              <td>{{ venta.factura }}</td>
              <td>{{ venta.fecha }}</td>
              <td>
                <button @click="verDetalleVenta(venta.factura)" class="btn btn-info">Detalle</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Detalle de la Factura de Venta -->
    <section v-if="detalleVenta.length" class="detalle-venta form-section">
      <h3>Detalle de la Factura de Venta {{ facturaSeleccionada }}</h3>
      <div class="form-actions">
        <button @click="exportarDetalleExcel">Exportar <font-awesome-icon icon="file-excel" class="excel-icon" /></button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Cantidad</th>
              <th>Bodega de Venta</th>
              <th>Precio Unitario</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in detalleVenta" :key="item.id">
              <td>{{ item.codigo }}</td>
              <td>{{ item.nombre }}</td>
              <td>{{ item.cantidad }}</td>
              <td>{{ item.bodega }}</td>
              <td>{{ item.precio_unitario !== null ? `$${item.precio_unitario.toFixed(2)}` : 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from '@/api/axios';
import * as XLSX from 'xlsx';

export default {
  name: 'CargarVentasManual',
  setup() {
    const router = useRouter();

    const archivoCsv = ref(null);
    const inputCsv = ref(null);
    const errores = ref([]);
    const filtroFactura = ref('');
    const fechaInicio = ref('');
    const fechaFin = ref('');
    const filtroBodega = ref('');
    const facturas = ref([]);
    const bodegas = ref([]);
    const resultadosVentas = ref([]);
    const detalleVenta = ref([]);
    const facturaSeleccionada = ref('');
    const isProcessing = ref(false);
    const isSyncActive = ref(false);

    const verificarSincronizacion = async () => {
      try {
        const response = await axios.get('/inventory/verificar-sincronizacion');
        isSyncActive.value = response.data.sync_analisis_inventario;
      } catch (error) {
        console.error('Error al verificar sincronización:', error);
        errores.value = ['No se pudo verificar la sincronización con el módulo de Análisis.'];
      }
    };

    const cargarCsv = (event) => {
      archivoCsv.value = event.target.files[0];
      errores.value = [];
    };

    const procesarCsv = async () => {
      if (!archivoCsv.value) {
        errores.value = ['Seleccione un archivo CSV para cargar'];
        return;
      }

      isProcessing.value = true;
      const formData = new FormData();
      formData.append('file', archivoCsv.value);

      try {
        const response = await axios.post('/inventory/ventas', formData);
        errores.value = [];
        alert(response.data.message);
        cargarFacturas();
        limpiarSesionCsv();
      } catch (error) {
        console.error('Error al cargar ventas:', error);
        if (error.response?.data?.errors) {
          errores.value = error.response.data.errors;
        } else {
          errores.value = [error.response?.data?.message || 'Ocurrió un error al cargar las ventas.'];
        }
        if (error.response?.status === 401) {
          router.push('/login');
        }
      } finally {
        isProcessing.value = false;
      }
    };

    const descargarPlantilla = () => {
      const csvData = [
        ['factura', 'codigo', 'nombre', 'cantidad', 'fecha_venta', 'bodega', 'precio_unitario'],
        ['FB1234567', 'PROD001', 'ARROZ ESPECIAL PERSONAL', '10', '2025-04-28 10:00:00', 'Almacen principal', '5000.00'],
        ['CC8901234', 'PROD002', 'PASTA ESPECIAL PERSONAL', '5', '2025-04-28 11:30:00', 'Bodega Norte', ''],
      ];
      const csvContent = csvData.map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', 'plantilla_cargue_ventas.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const limpiarSesionCsv = () => {
      archivoCsv.value = null;
      if (inputCsv.value) inputCsv.value.value = '';
    };

    const limpiarPagina = () => {
      limpiarSesionCsv();
      errores.value = [];
      filtroFactura.value = '';
      fechaInicio.value = '';
      fechaFin.value = '';
      filtroBodega.value = '';
      resultadosVentas.value = [];
      detalleVenta.value = [];
      facturaSeleccionada.value = '';
    };

    const cargarFacturas = async () => {
      try {
        const response = await axios.get('/inventory/ventas-facturas');
        facturas.value = response.data.facturas;
      } catch (error) {
        console.error('Error al cargar facturas:', error);
        alert('Ocurrió un error al cargar las facturas.');
      }
    };

    const cargarBodegas = async () => {
      try {
        const response = await axios.get('/inventory/bodegas');
        bodegas.value = response.data;
      } catch (error) {
        console.error('Error al cargar bodegas:', error);
        alert('Ocurrió un error al cargar las bodegas.');
      }
    };

    const consultarVentas = async () => {
      try {
        const params = {
          factura: filtroFactura.value || undefined,
          fecha_inicio: fechaInicio.value || undefined,
          fecha_fin: fechaFin.value || undefined,
          bodega_id: filtroBodega.value || undefined,
        };
        const response = await axios.get('/inventory/consultar-ventas', { params });
        resultadosVentas.value = response.data;
        detalleVenta.value = [];
      } catch (error) {
        console.error('Error al consultar facturas de venta:', error);
        alert('Ocurrió un error al consultar las facturas.');
      }
    };

    const verDetalleVenta = async (factura) => {
      try {
        facturaSeleccionada.value = factura;
        const response = await axios.get('/inventory/detalle-venta', {
          params: { factura }
        });
        detalleVenta.value = response.data;
      } catch (error) {
        console.error('Error al obtener detalle de la factura:', error);
        alert('No se pudo recuperar el detalle de la factura.');
      }
    };

    const exportarListadoExcel = () => {
      if (!resultadosVentas.value.length) {
        alert('No hay datos para exportar a Excel.');
        return;
      }

      const bodegaNombre = bodegas.value.find(b => b.id === filtroBodega.value)?.nombre || 'Todas';

      const worksheetData = [
        ['Resultado de consulta de Facturas de Ventas Cargadas'],
        [`Número de Factura: ${filtroFactura.value || 'Todos'}`],
        [`Fecha Inicio: ${fechaInicio.value || 'No especificada'}`],
        [`Fecha Fin: ${fechaFin.value || 'No especificada'}`],
        [`Bodega: ${bodegaNombre}`],
        [],
        ['Número de Factura', 'Fecha y Hora'],
        ...resultadosVentas.value.map(venta => [venta.factura, venta.fecha])
      ];

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Facturas');
      XLSX.writeFile(workbook, `facturas_ventas_${new Date().toISOString().slice(0, 10)}.xlsx`);
    };

    const exportarDetalleExcel = () => {
      if (!detalleVenta.value.length) {
        alert('No hay datos para exportar a Excel.');
        return;
      }

      const fechaCargue = resultadosVentas.value.find(v => v.factura === facturaSeleccionada.value)?.fecha || 'Desconocida';

      const worksheetData = [
        [`Detalle Factura ${facturaSeleccionada.value}`],
        [`Fecha de Cargue: ${fechaCargue}`],
        [],
        ['Código', 'Nombre', 'Cantidad', 'Bodega de Venta', 'Precio Unitario'],
        ...detalleVenta.value.map(item => [
          item.codigo,
          item.nombre,
          item.cantidad,
          item.bodega,
          item.precio_unitario !== null ? item.precio_unitario.toFixed(2) : 'N/A'
        ])
      ];

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Detalle Factura');
      XLSX.writeFile(workbook, `detalle_factura_${facturaSeleccionada.value}.xlsx`);
    };

    onMounted(async () => {
      await verificarSincronizacion();
      if (!isSyncActive.value) {
        cargarFacturas();
        cargarBodegas();
      }
    });

    return {
      archivoCsv,
      inputCsv,
      errores,
      filtroFactura,
      fechaInicio,
      fechaFin,
      filtroBodega,
      facturas,
      bodegas,
      resultadosVentas,
      detalleVenta,
      facturaSeleccionada,
      isProcessing,
      isSyncActive,
      cargarCsv,
      procesarCsv,
      descargarPlantilla,
      limpiarPagina,
      cargarFacturas,
      cargarBodegas,
      consultarVentas,
      verDetalleVenta,
      exportarListadoExcel,
      exportarDetalleExcel
    };
  }
};
</script>

<style scoped>
.cargar-ventas {
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

h3 {
  font-size: 1.2rem;
  color: #34495e;
  margin-bottom: 15px;
}

p {
  font-size: 1rem;
  color: #34495e;
  margin-bottom: 15px;
}

.sync-warning {
  background: #fff3cd;
  border: 1px solid #ffeeba;
  color: #856404;
}

.menu-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  justify-content: flex-end;
}

button, .btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled), .btn:hover {
  background-color: #2c3e50;
}

.btn-warning {
  background-color: #ffc107;
  color: #333;
}

.btn-warning:hover {
  background-color: #e0a800;
}

.btn-info {
  background-color: #17a2b8;
}

.btn-info:hover {
  background-color: #138496;
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

.form-group input, .form-group select {
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

th, td {
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

ul {
  margin-top: 10px;
  padding-left: 20px;
}

li {
  color: #e74c3c;
  font-size: 14px;
}

@media (max-width: 768px) {
  .menu-buttons {
    flex-direction: column;
    align-items: flex-end;
  }

  .form-group input, .form-group select {
    font-size: 16px;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>