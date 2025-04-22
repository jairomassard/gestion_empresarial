<template>
    <div class="cargar-compras">
      <h1>Compra de Productos</h1>
  
      <section class="menu-buttons">
        <!--<button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú</button>-->
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
      </section>
  
      <!-- Subida de Archivo CSV -->
      <section class="form-section">
        <h2>Subir Archivo</h2>
        <div class="form-group">
          <label for="inputCsv">Archivo CSV:</label>
          <input id="inputCsv" type="file" @change="cargarCsv" ref="inputCsv" />
        </div>
        <button @click="procesarCsv">Cargar Compras de Productos</button>
      </section>
  
      <!-- Descarga de Plantilla -->
      <section class="form-section">
        <h2>Descargar Plantilla</h2>
        <button @click="descargarPlantilla">Descargar</button>
      </section>
  
      <!-- Consulta de Facturas -->
      <section class="consulta-facturas form-section">
        <h2>Consulta de Facturas de Compra</h2>
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
          <label for="selectorFactura">Seleccionar Factura:</label>
          <select v-model="filtroFactura" id="selectorFactura">
            <option value="" disabled>Seleccione una factura</option>
            <option v-for="factura in facturas" :key="factura" :value="factura">{{ factura }}</option>
          </select>
        </div>
        <button @click="consultarFacturas">Consultar Facturas</button>
      </section>
  
      <!-- Resultados de la Consulta -->
      <section v-if="resultadosFacturas.length" class="resultados-facturas form-section">
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
              <tr v-for="factura in resultadosFacturas" :key="factura.factura">
                <td>{{ factura.factura }}</td>
                <td>{{ factura.fecha }}</td>
                <td>
                  <button @click="verDetalleFactura(factura.factura)" class="btn btn-info">Detalle</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
  
      <!-- Detalle de la Factura -->
      <section v-if="detalleFactura.length" class="detalle-factura form-section">
        <h3>Detalle de la Factura de Compra {{ facturaSeleccionada }}</h3>
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
                <th>Bodega</th>
                <th>Costo Unitario</th>
                <th>Costo Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in detalleFactura" :key="item.id">
                <td>{{ item.codigo }}</td>
                <td>{{ item.nombre }}</td>
                <td>{{ item.cantidad }}</td>
                <td>{{ item.bodega }}</td>
                <td>{{ item.costo_unitario ? `$${item.costo_unitario.toFixed(2)}` : 'N/A' }}</td>
                <td>{{ item.costo_total ? `$${item.costo_total.toFixed(2)}` : 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
  
      <!-- Mostrar errores -->
      <section v-if="errores.length" class="form-section">
        <h2>Errores Detectados:</h2>
        <ul>
          <li v-for="(error, index) in errores" :key="index">{{ error }}</li>
        </ul>
      </section>
    </div>
  </template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from '@/api/axios';
import * as XLSX from 'xlsx';

export default {
  name: 'CargarComprasProducto',
  setup() {
    const router = useRouter();

    const archivoCsv = ref(null);
    const inputCsv = ref(null);
    const errores = ref([]);
    const filtroFactura = ref('');
    const fechaInicio = ref('');
    const fechaFin = ref('');
    const facturas = ref([]);
    const resultadosFacturas = ref([]);
    const detalleFactura = ref([]);
    const facturaSeleccionada = ref('');

    const cargarCsv = (event) => {
      archivoCsv.value = event.target.files[0];
    };

    const procesarCsv = async () => {
      if (!archivoCsv.value) {
        alert('Seleccione un archivo para cargar');
        return;
      }

      const formData = new FormData();
      formData.append('file', archivoCsv.value);

      try {
        const response = await axios.post('/inventory/cargar-compras', formData);
        alert(response.data.message);
        errores.value = [];
        cargarFacturas();
        limpiarSesionCsv();
      } catch (error) {
        console.error('Error al cargar compras:', error);
        if (error.response?.data?.errors) {
          errores.value = error.response.data.errors;
        } else {
          alert('Ocurrió un error al cargar las compras.');
        }
      }
    };

    const descargarPlantilla = () => {
      const csvData = [
        ['factura', 'codigo', 'nombre', 'cantidad', 'bodega', 'contenedor', 'fecha_ingreso', 'costo_unitario'],
        ['FAC001', 'GRA05299901000000', 'R5 BULK PASTEL YELLOW', '100', 'Bodega1', 'CONT001', '2024-12-01 10:00:00', '50.00'],
        ['ABC123', 'GRA05299909000000', 'R5 BULK PASTEL LIGTH PINK', '150', 'Bodega2', 'CONT002', '2024-12-01 10:30:00', '45.00'],
      ];
      const csvContent = csvData.map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', 'plantilla_cargue_compras.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const volverAlMenu = () => {
      router.push('/inventory');
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
      resultadosFacturas.value = [];
      detalleFactura.value = [];
      facturaSeleccionada.value = '';
    };

    const cargarFacturas = async () => {
      try {
        const response = await axios.get('/inventory/facturas');
        facturas.value = response.data.facturas;
      } catch (error) {
        console.error('Error al cargar facturas:', error);
        alert('Ocurrió un error al cargar las facturas.');
      }
    };

    const consultarFacturas = async () => {
      try {
        const params = {
          factura: filtroFactura.value || undefined,
          fecha_inicio: fechaInicio.value || undefined,
          fecha_fin: fechaFin.value || undefined,
        };
        const response = await axios.get('/inventory/consultar-facturas', { params });
        resultadosFacturas.value = response.data;
        detalleFactura.value = [];
      } catch (error) {
        console.error('Error al consultar facturas:', error);
        alert('Ocurrió un error al consultar las facturas.');
      }
    };

    const verDetalleFactura = async (factura) => {
      try {
        facturaSeleccionada.value = factura;
        const response = await axios.get('/inventory/detalle-factura', {
          params: { factura }
        });
        detalleFactura.value = response.data;
      } catch (error) {
        console.error('Error al obtener detalle de factura:', error);
        alert('No se pudo recuperar el detalle de la factura.');
      }
    };

    const exportarListadoExcel = () => {
      if (!resultadosFacturas.value.length) {
        alert('No hay datos para exportar a Excel.');
        return;
      }

      const worksheetData = [
        ['Resultado de consulta de Facturas de Compras Cargadas'],
        [`Número de Factura: ${filtroFactura.value || 'Todos'}`],
        [`Fecha Inicio: ${fechaInicio.value || 'No especificada'}`],
        [`Fecha Fin: ${fechaFin.value || 'No especificada'}`],
        [],
        ['Número de Factura', 'Fecha y Hora'],
        ...resultadosFacturas.value.map(factura => [factura.factura, factura.fecha])
      ];

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Facturas');
      XLSX.writeFile(workbook, `facturas_compras_${new Date().toISOString().slice(0, 10)}.xlsx`);
    };

    const exportarDetalleExcel = () => {
      if (!detalleFactura.value.length) {
        alert('No hay datos para exportar a Excel.');
        return;
      }

      const fechaCargue = resultadosFacturas.value.find(f => f.factura === facturaSeleccionada.value)?.fecha || 'Desconocida';

      const worksheetData = [
        [`Detalle Factura ${facturaSeleccionada.value}`],
        [`Fecha de Cargue: ${fechaCargue}`],
        [],
        ['Código', 'Nombre', 'Cantidad', 'Bodega', 'Costo Unitario', 'Costo Total'],
        ...detalleFactura.value.map(item => [
          item.codigo,
          item.nombre,
          item.cantidad,
          item.bodega,
          item.costo_unitario || 'N/A',
          item.costo_total || 'N/A'
        ])
      ];

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Detalle Factura');
      XLSX.writeFile(workbook, `detalle_factura_${facturaSeleccionada.value}.xlsx`);
    };

    onMounted(() => {
      cargarFacturas();
    });

    return {
      archivoCsv,
      inputCsv,
      errores,
      filtroFactura,
      fechaInicio,
      fechaFin,
      facturas,
      resultadosFacturas,
      detalleFactura,
      facturaSeleccionada,
      cargarCsv,
      procesarCsv,
      descargarPlantilla,
      volverAlMenu,
      limpiarPagina,
      cargarFacturas,
      consultarFacturas,
      verDetalleFactura,
      exportarListadoExcel,
      exportarDetalleExcel
    };
  }
};
</script>

<style scoped>
.cargar-compras {
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

button:hover, .btn:hover {
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
  color: #555;
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