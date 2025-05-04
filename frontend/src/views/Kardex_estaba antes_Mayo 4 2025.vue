
<template>
  <div class="kardex-view">
    <h1>Kardex de Inventario de Productos</h1>

    <!-- Botones de acción -->
    <div class="actions" style="justify-content: flex-end">

      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Filtros de búsqueda -->
    <section class="filters form-section">
      <h2>Filtrar Movimientos</h2>
      <div class="filters-header">
        <div class="form-group">
          <label for="fechaInicio">Fecha inicio:</label>
          <input type="date" id="fechaInicio" v-model="fechaInicio" />
        </div>
        <div class="form-group">
          <label for="fechaFin">Fecha fin:</label>
          <input type="date" id="fechaFin" v-model="fechaFin" />
        </div>
        <div class="form-actions">
          <button @click="consultarKardex" class="btn">Consultar Kardex</button>
        </div>
      </div>

      <div class="filters-products form-group">
        <label for="nombreProducto">Buscar por nombre:</label>
        <input
          type="text"
          id="nombreProducto"
          v-model="nombreProducto"
          placeholder="Ingrese nombre del producto"
          @input="sincronizarPorNombre"
        />
      </div>
      <div class="filters-products form-group">
        <label for="productoSelector">Seleccione un producto:</label>
        <select v-model="codigoProducto" id="productoSelector" @change="sincronizarSelectorConCodigo">
          <option value="" disabled>Seleccione un producto</option>
          <option v-for="producto in productos" :key="producto.codigo" :value="producto.codigo">
            {{ producto.codigo }} - {{ producto.nombre }}
          </option>
        </select>
      </div>
      <div class="filters-products form-group">
        <label for="codigoProducto">O ingrese el código del producto:</label>
        <input
          type="text"
          id="codigoProducto"
          v-model="codigoProducto"
          placeholder="Ingrese el código del producto"
          @input="sincronizarCodigoConSelector"
        />
      </div>
    </section>

    <!-- Mensaje informativo -->
    <p class="info-message">
      Nota: Para incluir movimientos del día actual, seleccione un día adicional como fecha final.
    </p>

    <!-- Tabla de resumen -->
    <section v-if="kardex.length" class="summary form-section">
      <h2>Resumen por Almacén</h2>
      <div class="cpp-global">
        <span>CPP GLOBAL</span>
        <span>{{ cppGlobal ? `$${formatCosto(cppGlobal)}` : 'N/A' }}</span>
      </div>
      <div class="table-container">
        <table class="resumen-costos">
          <thead>
            <tr>
              <th>ALMACÉN</th>
              <th>STOCK FINAL</th>
              <th>VALOR ACUMULADO</th>
              <th>CPP</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(resumen, index) in resumenPorAlmacen" :key="index">
              <td>{{ resumen.almacen }}</td>
              <td>{{ resumen.stockFinal }}</td>
              <td>{{ resumen.valorAcumulado ? `$${formatCosto(resumen.valorAcumulado)}` : 'N/A' }}</td>
              <td>{{ resumen.cpp ? `$${formatCosto(resumen.cpp)}` : 'N/A' }}</td>
            </tr>
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ totalStock }}</strong></td>
              <td><strong>{{ totalValor ? `$${formatCosto(totalValor)}` : 'N/A' }}</strong></td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Filtro por almacén -->
    <section v-if="kardex.length" class="filters-bodega form-section">
      <h3>Filtrar por Almacén</h3>
      <div class="bodega-checkboxes">
        <label class="checkbox-container">
          <input
            type="checkbox"
            value=""
            v-model="bodegasSeleccionadas"
            @change="filtrarPorBodega"
          />
          <span>Todos</span>
        </label>
        <label v-for="bodega in bodegas" :key="bodega.id" class="checkbox-container">
          <input
            type="checkbox"
            :value="bodega.nombre"
            v-model="bodegasSeleccionadas"
            @change="filtrarPorBodega"
          />
          <span>{{ bodega.nombre }}</span>
        </label>
      </div>
    </section>

    <!-- Tabla de resultados -->
    <section v-if="kardexFiltrado.length" class="results form-section">
      <h2>Movimientos del Producto</h2>
      <div class="form-actions">
        <button @click="imprimirKardexPDF" class="btn btn-success" title="Imprimir PDF">
          <font-awesome-icon icon="file-pdf" class="pdf-icon" />
        </button>
        <button @click="exportarKardexCSV" class="btn btn-info" title="Exportar CSV">
          <font-awesome-icon icon="file-csv" class="csv-icon" />
        </button>
        <button @click="exportarKardexExcel" class="btn btn-primary" title="Exportar Excel">
          <font-awesome-icon icon="file-excel" class="excel-icon" />
        </button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Documento</th>
              <th>Almacén</th>
              <th>Cant.</th>
              <th>Costo</th>
              <th>Costo Total</th>
              <th>Cantidad Acumulada</th>
              <th>Valor Acumulado</th>
              <th>CPP</th>
              <th>CPP Global</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(registro, index) in kardexFiltrado" :key="index">
              <td>{{ registro.fecha }}</td>
              <td>{{ registro.tipo }}</td>
              <td>{{ registro.bodega || 'N/A' }}</td>
              <td>{{ registro.tipo === 'SALIDA' ? `-${registro.cantidad}` : registro.cantidad }}</td>
              <td>{{ registro.costo_unitario ? `$${formatCosto(registro.costo_unitario)}` : 'N/A' }}</td>
              <td>{{ registro.tipo === 'SALIDA' ? `-$${formatCosto(registro.costo_total)}` : `$${formatCosto(registro.costo_total)}` }}</td>
              <td>{{ registro.saldo }}</td>
              <td>{{ registro.saldo_costo_total !== null && registro.saldo_costo_total !== undefined ? `$${formatCosto(registro.saldo_costo_total)}` : 'N/A' }}</td>
              <td>{{ registro.saldo_costo_unitario ? `$${formatCosto(registro.saldo_costo_unitario)}` : 'N/A' }}</td>
              <td>{{ registro.saldo_costo_unitario_global ? `$${formatCosto(registro.saldo_costo_unitario_global)}` : 'N/A' }}</td>
              <td>{{ registro.descripcion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Sin resultados -->
    <section v-else-if="mostrarMensajeSinDatos" class="form-section">
      <p>No hay datos para mostrar. Realice una consulta o ajuste el filtro por almacén.</p>
    </section>
  </div>
</template>

<script>
import apiClient from '@/api/axios';
import * as XLSX from 'xlsx';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  name: 'KardexView',
  components: { FontAwesomeIcon },
  data() {
    return {
      productos: [],
      bodegas: [],
      codigoProducto: '',
      nombreProducto: '',
      fechaInicio: '',
      fechaFin: '',
      kardex: [],
      kardexFiltrado: [],
      bodegasSeleccionadas: [],
      resumenPorAlmacen: [],
      cppGlobal: null,
      totalStock: 0,
      totalValor: 0,
      mostrarMensajeSinDatos: false,
    };
  },
  methods: {
    limpiarPagina() {
      this.codigoProducto = '';
      this.nombreProducto = '';
      this.fechaInicio = '';
      this.fechaFin = '';
      this.kardex = [];
      this.kardexFiltrado = [];
      this.bodegasSeleccionadas = [];
      this.resumenPorAlmacen = [];
      this.cppGlobal = null;
      this.totalStock = 0;
      this.totalValor = 0;
      this.mostrarMensajeSinDatos = false;
    },
    async cargarProductos() {
      try {
        const response = await apiClient.get('/api/productos/completos');
        this.productos = response.data.sort((a, b) => a.codigo.localeCompare(b.codigo));
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message;
        alert(`Error al cargar productos: ${errorMsg}`);
      }
    },
    async cargarBodegas() {
      try {
        const response = await apiClient.get('/inventory/bodegas');
        this.bodegas = response.data;
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message;
        alert(`Error al cargar almacenes: ${errorMsg}`);
      }
    },
    async consultarKardex() {
      if (!this.codigoProducto || !this.fechaInicio || !this.fechaFin) {
        alert('Debe seleccionar un producto y definir un rango de fechas.');
        return;
      }

      try {
        const params = {
          codigo: this.codigoProducto,
          fecha_inicio: this.fechaInicio,
          fecha_fin: this.fechaFin,
        };
        if (this.bodegasSeleccionadas.length > 0 && !this.bodegasSeleccionadas.includes('')) {
          params.bodegas = this.bodegasSeleccionadas.join(',');
        }

        const response = await apiClient.get('/inventory/kardex', { params });
        const data = response.data;

        if (data.message) {
          alert(data.message);
          this.kardex = [];
          this.kardexFiltrado = [];
          this.mostrarMensajeSinDatos = true;
          return;
        }

        this.kardex = data.kardex || [];
        this.kardexFiltrado = [...this.kardex];
        this.calcularResumen();
        this.mostrarMensajeSinDatos = this.kardex.length === 0;
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;
        alert(`Error al consultar el kardex: ${errorMsg}`);
        this.kardex = [];
        this.kardexFiltrado = [];
        this.mostrarMensajeSinDatos = true;
      }
    },
    calcularResumen() {
      const almacenes = [...new Set(this.kardex.map((mov) => mov.bodega))].filter((b) => b);
      this.resumenPorAlmacen = almacenes
        .map((almacen) => {
          const movimientosAlmacen = this.kardex
            .filter((mov) => mov.bodega === almacen)
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
          const ultimoMovimiento = movimientosAlmacen[0];
          return {
            almacen,
            stockFinal: ultimoMovimiento.saldo,
            valorAcumulado: ultimoMovimiento.saldo_costo_total,
            cpp: ultimoMovimiento.saldo_costo_unitario,
          };
        })
        .sort((a, b) => a.almacen.localeCompare(b.almacen));

      this.totalStock = this.resumenPorAlmacen.reduce((sum, r) => sum + r.stockFinal, 0);
      this.totalValor = this.resumenPorAlmacen.reduce((sum, r) => sum + (r.valorAcumulado || 0), 0);
      this.cppGlobal = this.totalStock > 0 ? this.totalValor / this.totalStock : 0;
    },
    filtrarPorBodega() {
      if (this.bodegasSeleccionadas.includes('')) {
        this.kardexFiltrado = [...this.kardex];
      } else if (this.bodegasSeleccionadas.length === 0) {
        this.kardexFiltrado = [...this.kardex];
      } else {
        this.kardexFiltrado = this.kardex.filter((mov) =>
          this.bodegasSeleccionadas.includes(mov.bodega)
        );
      }
      this.mostrarMensajeSinDatos = this.kardexFiltrado.length === 0 && this.kardex.length > 0;
    },
    async imprimirKardexPDF() {
      if (!this.codigoProducto || !this.fechaInicio || !this.fechaFin) {
        alert('Debe realizar una consulta antes de generar el PDF.');
        return;
      }
      try {
        const params = {
          codigo: this.codigoProducto,
          fecha_inicio: this.fechaInicio,
          fecha_fin: this.fechaFin,
        };
        if (this.bodegasSeleccionadas.length > 0 && !this.bodegasSeleccionadas.includes('')) {
          params.bodegas = this.bodegasSeleccionadas.join(',');
        }
        const response = await apiClient.get('/api/kardex/pdf', {
          params,
          responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute(
          'download',
          `kardex_${this.codigoProducto}${this.bodegasSeleccionadas.length ? '_' + this.bodegasSeleccionadas.join('_') : ''}.pdf`
        );
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message;
        alert(`Error al generar el PDF del Kardex: ${errorMsg}`);
      }
    },
    exportarKardexCSV() {
      if (!this.kardexFiltrado.length) {
        alert('No hay datos filtrados para exportar a CSV.');
        return;
      }
      const productoNombre =
        this.productos.find((p) => p.codigo === this.codigoProducto)?.nombre || 'Desconocido';
      let csvContent =
        'data:text/csv;charset=utf-8,' +
        `Kardex de Inventario\n` +
        `Producto: ${this.codigoProducto} - ${productoNombre}\n` +
        `Rango de Fechas: ${this.fechaInicio} a ${this.fechaFin}\n` +
        `Almacén: ${this.bodegasSeleccionadas.length > 0 && !this.bodegasSeleccionadas.includes('') ? this.bodegasSeleccionadas.join(', ') : 'Todos'}\n\n` +
        `Resumen por Almacén\n` +
        `CPP GLOBAL;${this.cppGlobal ? this.cppGlobal.toFixed(2) : 'N/A'}\n\n` +
        `ALMACÉN;STOCK FINAL;VALOR ACUMULADO;CPP\n` +
        this.resumenPorAlmacen
          .map(
            (resumen) =>
              `${resumen.almacen};${resumen.stockFinal};${resumen.valorAcumulado ? resumen.valorAcumulado.toFixed(2) : 'N/A'};${resumen.cpp ? resumen.cpp.toFixed(2) : 'N/A'}`
          )
          .join('\n') +
        '\n' +
        `TOTAL;${this.totalStock};${this.totalValor ? this.totalValor.toFixed(2) : 'N/A'};\n\n` +
        `Movimientos del Producto\n` +
        `Fecha;Documento;Almacén;Cant.;Costo;Costo Total;Cantidad Acumulada;Valor Acumulado;CPP;CPP Global;Descripción\n` +
        this.kardexFiltrado
          .map((mov) => [
            mov.fecha,
            mov.tipo,
            mov.bodega || 'N/A',
            mov.tipo === 'SALIDA' ? -mov.cantidad : mov.cantidad,
            mov.costo_unitario ? mov.costo_unitario.toFixed(2) : 'N/A',
            mov.tipo === 'SALIDA' ? -mov.costo_total : mov.costo_total ? mov.costo_total.toFixed(2) : 'N/A',
            mov.saldo,
            mov.saldo_costo_total !== undefined && mov.saldo_costo_total !== null
              ? mov.saldo_costo_total.toFixed(2)
              : 'N/A',
            mov.saldo_costo_unitario ? mov.saldo_costo_unitario.toFixed(2) : 'N/A',
            mov.saldo_costo_unitario_global ? mov.saldo_costo_unitario_global.toFixed(2) : 'N/A',
            mov.descripcion.replace(/;/g, ' '),
          ].join(';'))
          .join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute(
        'download',
        `kardex_${this.codigoProducto}${this.bodegasSeleccionadas.length ? '_' + this.bodegasSeleccionadas.join('_') : ''}.csv`
      );
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    exportarKardexExcel() {
      if (!this.kardexFiltrado.length) {
        alert('No hay datos filtrados para exportar a Excel.');
        return;
      }
      const productoNombre =
        this.productos.find((p) => p.codigo === this.codigoProducto)?.nombre || 'Desconocido';
      const worksheetData = [
        ['Kardex de Inventario'],
        [`Producto: ${this.codigoProducto} - ${productoNombre}`],
        [`Rango de Fechas: ${this.fechaInicio} a ${this.fechaFin}`],
        [
          `Almacén: ${
            this.bodegasSeleccionadas.length > 0 && !this.bodegasSeleccionadas.includes('')
              ? this.bodegasSeleccionadas.join(', ')
              : 'Todos'
          }`,
        ],
        [],
        ['Resumen por Almacén'],
        ['CPP GLOBAL', this.cppGlobal ? this.cppGlobal.toFixed(2) : 'N/A'],
        [],
        ['ALMACÉN', 'STOCK FINAL', 'VALOR ACUMULADO', 'CPP'],
        ...this.resumenPorAlmacen.map((resumen) => [
          resumen.almacen,
          resumen.stockFinal,
          resumen.valorAcumulado ? resumen.valorAcumulado.toFixed(2) : 'N/A',
          resumen.cpp ? resumen.cpp.toFixed(2) : 'N/A',
        ]),
        ['TOTAL', this.totalStock, this.totalValor ? this.totalValor.toFixed(2) : 'N/A', ''],
        [],
        ['Movimientos del Producto'],
        [
          'Fecha',
          'Documento',
          'Almacén',
          'Cant.',
          'Costo',
          'Costo Total',
          'Cant. Acumulada',
          'Valor Acumulado',
          'CPP',
          'CPP Global',
          'Descripción',
        ],
        ...this.kardexFiltrado.map((mov) => [
          mov.fecha,
          mov.tipo,
          mov.bodega || 'N/A',
          mov.tipo === 'SALIDA' ? -mov.cantidad : mov.cantidad,
          mov.costo_unitario ? mov.costo_unitario.toFixed(2) : 'N/A',
          mov.tipo === 'SALIDA' ? -mov.costo_total : mov.costo_total ? mov.costo_total.toFixed(2) : 'N/A',
          mov.saldo,
          mov.saldo_costo_total !== undefined && mov.saldo_costo_total !== null
            ? mov.saldo_costo_total.toFixed(2)
            : 'N/A',
          mov.saldo_costo_unitario ? mov.saldo_costo_unitario.toFixed(2) : 'N/A',
          mov.saldo_costo_unitario_global ? mov.saldo_costo_unitario_global.toFixed(2) : 'N/A',
          mov.descripcion,
        ]),
      ];
      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Kardex');
      XLSX.writeFile(
        workbook,
        `kardex_${this.codigoProducto}${this.bodegasSeleccionadas.length ? '_' + this.bodegasSeleccionadas.join('_') : ''}.xlsx`
      );
    },
    sincronizarPorNombre() {
      if (!this.nombreProducto) {
        this.codigoProducto = '';
        return;
      }
      const productoEncontrado = this.productos.find((p) =>
        p.nombre.toLowerCase().includes(this.nombreProducto.toLowerCase())
      );
      if (productoEncontrado) {
        this.codigoProducto = productoEncontrado.codigo;
      }
    },
    sincronizarCodigoConSelector() {
      if (!this.codigoProducto) {
        this.nombreProducto = '';
        return;
      }
      const productoEncontrado = this.productos.find((p) => p.codigo === this.codigoProducto);
      if (productoEncontrado) {
        this.nombreProducto = productoEncontrado.nombre;
      }
    },
    sincronizarSelectorConCodigo() {
      const productoEncontrado = this.productos.find((p) => p.codigo === this.codigoProducto);
      if (productoEncontrado) {
        this.nombreProducto = productoEncontrado.nombre;
      } else {
        this.nombreProducto = '';
      }
    },
    volverAlMenu() {
      this.$router.push('/inventory');
    },
    formatCosto(costo) {
      return Number(costo).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
  },
  mounted() {
    this.cargarProductos();
    this.cargarBodegas();
  },
};
</script>

<style scoped>
.kardex-view {
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
  margin-bottom: 10px;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

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

.btn-success {
  background-color: #28a745;
}

.btn-success:hover {
  background-color: #218838;
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

.form-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.filters-header {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.info-message {
  margin: 10px 0;
  font-style: italic;
  color: #555;
  text-align: center;
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
  width: 60%;
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

.cpp-global {
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  width: 200px;
}

.filters-bodega {
  padding: 15px;
}

.bodega-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 10px 0;
}

.checkbox-container {
  display: flex;
  align-items: center;
  gap: 5px;
}

.checkbox-container input[type='checkbox'] {
  margin: 0;
  accent-color: #42b983;
}

.checkbox-container span {
  font-size: 14px;
  color: #333;
}

.checkbox-container:hover span {
  color: #42b983;
}

.excel-icon,
.pdf-icon,
.csv-icon {
  margin-left: 5px;
}

@media (max-width: 768px) {
  .filters-header {
    flex-direction: column;
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

  .resumen-costos {
    width: 100%;
  }
}
</style>