<template>
    <div class="cargar-notas-credito">
      <h1>Cargar Notas Crédito</h1>
  
      <section class="menu-buttons">
        <!--<button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button> -->
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
      </section>
  
      <!-- Subida de Archivo CSV -->
      <section class="form-section" v-if="hasPermission('inventario', 'notas_credito', 'editar')">
        <h2>Subir Archivo CSV</h2>
        <div class="form-group">
          <label for="inputCsv">Archivo CSV:</label>
          <input id="inputCsv" type="file" @change="cargarCsv" ref="inputCsv" />
          <p>El CSV debe incluir: nota_credito, factura, codigo, nombre, cantidad, fecha_devolucion</p>
        </div>
        <button @click="procesarCsv">Cargar Notas Crédito</button>
      </section>
      <section class="form-section" v-else>
        <p>No tienes permiso para cargar notas de crédito.</p>
      </section>
  
      <!-- Mostrar Errores -->
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
  
      <!-- Consulta de Notas Crédito -->
      <section class="consulta-notas-credito form-section">
        <h2>Consulta de Notas Crédito</h2>
        <div class="form-group">
          <label for="filtroNotaCredito">Número de Nota Crédito:</label>
          <input
            v-model="filtroNotaCredito"
            id="filtroNotaCredito"
            placeholder="Ingrese número de nota crédito"
          />
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
          <label for="selectorNotaCredito">Seleccionar Nota Crédito:</label>
          <select v-model="filtroNotaCredito" id="selectorNotaCredito">
            <option value="" disabled>Seleccione una nota crédito</option>
            <option v-for="nota in notasCredito" :key="nota" :value="nota">{{ nota }}</option>
          </select>
        </div>
        <button @click="consultarNotasCredito">Consultar Notas Crédito</button>
      </section>
  
      <!-- Resultados de la Consulta -->
      <section v-if="resultadosNotasCredito.length" class="resultados-notas-credito form-section">
        <h3>Resultados de la Consulta</h3>
        <div class="form-actions">
          <button @click="exportarListadoExcel">
            Exportar Listado <font-awesome-icon icon="file-excel" class="excel-icon" />
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Número de Nota Crédito</th>
                <th>Fecha y Hora</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="nota in resultadosNotasCredito" :key="nota.nota_credito">
                <td>{{ nota.nota_credito }}</td>
                <td>{{ nota.fecha }}</td>
                <td>
                  <button @click="verDetalleNotaCredito(nota.nota_credito)" class="btn btn-info">Detalle</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
  
      <!-- Detalle de la Nota Crédito -->
      <section v-if="detalleNotaCredito.length" class="detalle-nota-credito form-section">
        <h3>Detalle de la Nota Crédito {{ notaCreditoSeleccionada }}</h3>
        <div class="form-actions">
          <button @click="exportarDetalleExcel">
            Exportar <font-awesome-icon icon="file-excel" class="excel-icon" />
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Cantidad Devuelta</th>
                <th>Bodega</th>
                <th>Costo Unitario</th>
                <th>Costo Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in detalleNotaCredito" :key="item.codigo">
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
    </div>
  </template>
  
  <script>
  import { ref } from 'vue';
  import { useStore } from 'vuex';
  import { useRouter } from 'vue-router';
  import axios from '@/api/axios';
  import * as XLSX from 'xlsx';
  
  export default {
    name: 'CargarNotasCredito',
    setup() {
      const store = useStore();
      const router = useRouter();
  
      const archivoCsv = ref(null);
      const inputCsv = ref(null);
      const errores = ref([]);
      const filtroNotaCredito = ref('');
      const fechaInicio = ref('');
      const fechaFin = ref('');
      const notasCredito = ref([]);
      const resultadosNotasCredito = ref([]);
      const detalleNotaCredito = ref([]);
      const notaCreditoSeleccionada = ref('');
  
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
          const response = await axios.post('/api/cargar_notas_credito', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          alert(response.data.message);
          errores.value = [];
          cargarNotasCredito();
          limpiarSesionCsv();
        } catch (error) {
          console.error('Error al cargar notas crédito:', error);
          if (error.response && error.response.data.errors) {
            errores.value = error.response.data.errors;
          } else {
            alert('Ocurrió un error al cargar las notas crédito');
          }
        }
      };
  
      const limpiarSesionCsv = () => {
        archivoCsv.value = null;
        if (inputCsv.value) inputCsv.value.value = '';
      };
  
      const descargarPlantilla = () => {
        const csvData = [
          ['nota_credito', 'factura', 'codigo', 'nombre', 'cantidad', 'fecha_devolucion'],
          ['ABC123', 'FB1234567', 'PROD0051', 'GASEOSA 1.5 LT COCA COLA', '5', '2025-04-12 10:00:00'],
          ['NC001', 'FB1234567', 'PROD0051', 'GASEOSA 1.5 LT COCA COLA', '2', '2025-04-12 17:00:00'],
        ];
        const csvContent = csvData.map((e) => e.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', 'plantilla_cargue_notas_credito.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      };
  
      const volverAlMenu = () => {
        const tipoUsuario = localStorage.getItem('tipo_usuario');
        if (tipoUsuario === 'admin') {
          router.push('/inventory');
        } else if (tipoUsuario === 'gerente') {
          router.push('/inventory');
        } else {
          alert('Rol no reconocido. Contacta al administrador.');
          router.push('/inventory');
        }
      };
  
      const limpiarPagina = () => {
        limpiarSesionCsv();
        errores.value = [];
        filtroNotaCredito.value = '';
        fechaInicio.value = '';
        fechaFin.value = '';
        resultadosNotasCredito.value = [];
        detalleNotaCredito.value = [];
        notaCreditoSeleccionada.value = '';
      };
  
      const cargarNotasCredito = async () => {
        try {
          const response = await axios.get('/api/notas_credito');
          notasCredito.value = response.data.notas_credito;
        } catch (error) {
          console.error('Error al cargar notas crédito:', error);
          alert('No se pudo cargar la lista de notas de crédito.');
        }
      };
  
      const consultarNotasCredito = async () => {
        try {
          const params = {
            nota_credito: filtroNotaCredito.value || undefined,
            fecha_inicio: fechaInicio.value || undefined,
            fecha_fin: fechaFin.value || undefined,
          };
          const response = await axios.get('/api/consultar_notas_credito', { params });
          resultadosNotasCredito.value = response.data;
          detalleNotaCredito.value = [];
        } catch (error) {
          console.error('Error al consultar notas crédito:', error);
          alert('Ocurrió un error al consultar las notas crédito.');
        }
      };
  
      const verDetalleNotaCredito = async (notaCredito) => {
        try {
          notaCreditoSeleccionada.value = notaCredito;
          const response = await axios.get('/api/detalle_nota_credito', {
            params: { nota_credito: notaCredito },
          });
          detalleNotaCredito.value = response.data;
        } catch (error) {
          console.error('Error al obtener detalle de la nota crédito:', error);
          alert('No se pudo recuperar el detalle de la nota crédito.');
        }
      };
  
      const exportarListadoExcel = () => {
        if (!resultadosNotasCredito.value.length) {
          alert('No hay datos para exportar a Excel.');
          return;
        }
  
        const worksheetData = [
          ['Resultado de consulta de Notas Crédito Cargadas'],
          [`Número de Nota Crédito: ${filtroNotaCredito.value || 'Todas'}`],
          [`Fecha Inicio: ${fechaInicio.value || 'No especificada'}`],
          [`Fecha Fin: ${fechaFin.value || 'No especificada'}`],
          [], // Línea en blanco
          ['Número de Nota Crédito', 'Fecha y Hora'],
          ...resultadosNotasCredito.value.map((nota) => [nota.nota_credito, nota.fecha]),
        ];
  
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Notas Crédito');
        XLSX.writeFile(workbook, `notas_credito_${new Date().toISOString().slice(0, 10)}.xlsx`);
      };
  
      const exportarDetalleExcel = () => {
        if (!detalleNotaCredito.value.length) {
          alert('No hay datos para exportar a Excel.');
          return;
        }
  
        const fechaCargue =
          resultadosNotasCredito.value.find((n) => n.nota_credito === notaCreditoSeleccionada.value)?.fecha ||
          'Desconocida';
  
        const worksheetData = [
          [`Detalle Nota Crédito ${notaCreditoSeleccionada.value}`],
          [`Fecha de Cargue: ${fechaCargue}`],
          [], // Línea en blanco
          ['Código', 'Nombre', 'Cantidad Devuelta', 'Bodega', 'Costo Unitario', 'Costo Total'],
          ...detalleNotaCredito.value.map((item) => [
            item.codigo,
            item.nombre,
            item.cantidad,
            item.bodega,
            item.costo_unitario ? item.costo_unitario.toFixed(2) : 'N/A',
            item.costo_total ? item.costo_total.toFixed(2) : 'N/A',
          ]),
        ];
  
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Detalle Nota Crédito');
        XLSX.writeFile(workbook, `detalle_nota_credito_${notaCreditoSeleccionada.value}.xlsx`);
      };
  
      return {
        archivoCsv,
        inputCsv,
        errores,
        filtroNotaCredito,
        fechaInicio,
        fechaFin,
        notasCredito,
        resultadosNotasCredito,
        detalleNotaCredito,
        notaCreditoSeleccionada,
        hasPermission: store.getters.hasPermission,
        cargarCsv,
        procesarCsv,
        descargarPlantilla,
        volverAlMenu,
        limpiarPagina,
        cargarNotasCredito,
        consultarNotasCredito,
        verDetalleNotaCredito,
        exportarListadoExcel,
        exportarDetalleExcel,
      };
    },
    mounted() {
      if (this.hasPermission('inventario', 'notas_credito', 'ver')) {
        this.cargarNotasCredito();
      } else {
        alert('No tienes permiso para ver notas de crédito.');
      }
    },
  };
  </script>
  
  <style scoped>
  .cargar-notas-credito {
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
  
  .form-group input,
  .form-group select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .form-group p {
    margin-top: 5px;
    font-size: 14px;
    color: #555;
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