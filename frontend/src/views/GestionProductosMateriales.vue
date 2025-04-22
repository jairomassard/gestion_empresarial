<template>
    <div class="gestion-productos-materiales">
      <h1>Gestión de Productos y Materiales</h1>
      
      <!-- Botones superiores -->
      <div class="top-buttons">
        <!-- <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú</button>-->
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
      </div>
  
      <!-- Subida de Archivo CSV -->
      <section class="carga-csv">
        <h2>Cargar Productos desde archivo .CSV</h2>
        <!-- Indicador de carga -->
        <div v-if="isLoadingCarga" class="spinner-container">
          <div class="spinner"></div>
          <p>Procesando archivo CSV, por favor espera...</p>
        </div>
        <!-- Input para subir archivo -->
        <div class="carga-input">
          <input type="file" accept=".csv" @change="cargarCsv" ref="inputCsv" />
          <button @click="procesarCsv" :disabled="isLoadingCarga">Subir</button>
          <button @click="limpiarSesionCsv" :disabled="isLoadingCarga" class="btn-warning">Limpiar Sesión</button>
        </div>
        <!-- Enlaces para descargar plantilla e instructivo -->
        <div class="carga-links">
          <a @click="descargarPlantillaCSV" class="link-descarga">📥 Descargar Plantilla CSV</a>
          <a @click="mostrarInstructivo" class="link-instructivo">📖 Instructivo de Uso</a>
        </div>
        <!-- Mostrar errores -->
        <div v-if="erroresCsv" class="error-container">
          <h3>Errores Detectados</h3>
          <textarea readonly v-model="erroresCsv"></textarea>
          <button @click="copiarErrores">Copiar errores</button>
        </div>
        <!-- Modal para el instructivo -->
        <div v-if="mostrarModal" class="modal-instructivo">
          <div class="modal-contenido">
            <h3>📄 Instructivo de Uso para Carga de Productos</h3>
            <p>1️⃣ <strong>Código</strong>: Código único del producto. No debe repetirse.</p>
            <p>2️⃣ <strong>Nombre</strong>: Nombre del producto.</p>
            <p>3️⃣ <strong>Peso Total / Unidad</strong>: Obligatorio solo para productos Base.</p>
            <p>4️⃣ <strong>Código de Barras</strong>: Código de barras opcional.</p>
            <p>5️⃣ <strong>Es Producto Compuesto</strong>: "Sí" si el producto es compuesto, "No" si es producto Base.</p>
            <p>6️⃣ <strong>Stock Mínimo</strong>: Cantidad mínima de inventario (opcional, número entero o decimal).</p>
            <p>7️⃣ <strong>Cantidad Productos</strong>: Si el producto es Base, se coloca 0. Si es compuesto, indicar cuántos productos lo conforman.</p>
            <p>8️⃣ <strong>Código y Cantidad de Productos Compuestos</strong>: Se deben indicar los códigos y cantidades de los productos compuestos.</p>
            <button @click="cerrarModal" class="btn-cerrar">Cerrar</button>
          </div>
        </div>
      </section>

      <!-- Nueva sección: Actualización Masiva de Productos -->
      <section class="carga-csv">
        <h2>Actualización Masiva de Productos desde archivo .CSV</h2>
        <!-- Indicador de carga -->
        <div v-if="isLoadingActualizar" class="spinner-container">
          <div class="spinner"></div>
          <p>Procesando archivo CSV de actualización, por favor espera...</p>
        </div>
        <!-- Input para subir archivo -->
        <div class="carga-input">
          <input type="file" accept=".csv" @change="cargarArchivoActualizarCsv" ref="inputActualizarCsv" />
          <button @click="procesarActualizacionCsv" :disabled="!archivoActualizarCsv || isLoadingActualizar">Subir</button>
          <button @click="limpiarActualizarCsv" :disabled="!archivoActualizarCsv || isLoadingActualizar" class="btn-warning">Limpiar Sesión</button>
        </div>
        <!-- Enlaces para descargar plantilla e instructivo -->
        <div class="carga-links">
          <a @click="descargarPlantillaActualizarCSV" class="link-descarga">📥 Descargar Plantilla CSV</a>
          <a @click="mostrarInstructivoActualizar" class="link-instructivo">📖 Instructivo de Uso</a>
        </div>
        <!-- Mostrar errores -->
        <div v-if="erroresActualizarCsv" class="error-container">
          <h3>Errores Detectados</h3>
          <textarea readonly v-model="erroresActualizarCsv"></textarea>
          <button @click="copiarErroresActualizar">Copiar errores</button>
        </div>
        <!-- Modal para el instructivo de actualización -->
        <div v-if="mostrarModalActualizar" class="modal-instructivo">
          <div class="modal-contenido">
            <h3>📄 Instructivo para Actualizar Productos desde CSV</h3>
            <p>1️⃣ <strong>Código</strong>: Código del producto existente (obligatorio).</p>
            <p>2️⃣ <strong>Nombre</strong>: Nuevo nombre del producto (debe ser único).</p>
            <p>3️⃣ <strong>Peso Total (gr)</strong>: Peso total para productos base.</p>
            <p>4️⃣ <strong>Peso Unidad (gr)</strong>: Peso por unidad para productos base.</p>
            <p>5️⃣ <strong>Código de Barras</strong>: Código de barras (opcional).</p>
            <p>6️⃣ <strong>Es Producto Compuesto</strong>: "Sí" o "No".</p>
            <p>7️⃣ <strong>Stock Mínimo</strong>: Número entero o vacío (opcional).</p>
            <p>8️⃣ <strong>Cantidad Productos</strong>: Número de productos base para compuestos.</p>
            <p>9️⃣ <strong>Código1, Cantidad1, etc.</strong>: Materiales para productos compuestos.</p>
            <p>📝 <strong>Notas</strong>:</p>
            <p>- Los campos vacíos no modificarán los valores existentes.</p>
            <p>- Los productos base deben existir previamente en el sistema.</p>
            <p>- El campo nombre debe ser único en el sistema.</p>
            <button @click="cerrarModalActualizar" class="btn-cerrar">Cerrar</button>
          </div>
        </div>
      </section>
      
      <!-- Formulario para Crear/Editar Producto -->
      <section class="form-section">
        <h2>{{ modoEdicion ? 'Editar Producto' : 'Crear Producto' }}</h2>
        <form @submit.prevent="modoEdicion ? actualizarProducto() : crearProducto()">
          <div class="form-group">
            <label for="codigo">Código del Producto:</label>
            <input v-model="producto.codigo" id="codigo" required :disabled="modoEdicion" />
          </div>
          <div class="form-group">
            <label for="nombre">Nombre del Producto:</label>
            <input v-model="producto.nombre" id="nombre" required />
          </div>
          <div class="form-group">
            <label for="codigo_barras">Código de Barras:</label>
            <input v-model="producto.codigo_barras" id="codigo_barras" />
          </div>
          <div class="form-group">
            <label>Tipo de Producto:</label>
            <select v-model="producto.es_producto_compuesto">
              <option :value="false">Base</option>
              <option :value="true">Compuesto</option>
            </select>
          </div>
          <div class="form-group">
            <label for="peso_total">Peso Total en Gramos:</label>
            <input v-model.number="producto.peso_total_gr" id="peso_total" type="number" step="0.01"
              :required="!producto.es_producto_compuesto" :disabled="producto.es_producto_compuesto" />
          </div>
          <div class="form-group">
            <label for="peso_unidad">Peso por Unidad en Gramos:</label>
            <input v-model.number="producto.peso_unidad_gr" id="peso_unidad" type="number" step="0.01"
              :required="!producto.es_producto_compuesto" :disabled="producto.es_producto_compuesto" />
          </div>
          <div class="form-group">
            <label for="stock_minimo">Stock Mínimo:</label>
            <input v-model.number="producto.stock_minimo" id="stock_minimo" type="number" min="0" />
          </div>
          <div class="form-actions">
            <button v-if="!modoEdicion" type="submit">Crear Producto</button>
            <template v-else>
              <button type="submit">Guardar Producto</button>
              <button type="button" @click="cancelarEdicion">Cancelar</button>
              <button type="button" @click="limpiarSesion" class="btn-warning">Limpiar Sesión</button>
            </template>
          </div>
        </form>
      </section>
  
      <!-- Materiales del Producto Compuesto -->
      <section v-if="producto.es_producto_compuesto && producto.id" class="materiales-section">
        <h2>Materiales del Producto</h2>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Producto Base</th>
                <th>Cantidad</th>
                <th>Peso Unitario (g)</th>
                <th>Peso Total (g)</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(material, index) in materiales" :key="index">
                <td>
                  <input type="text" v-model="material.nombreDigitado" placeholder="Buscar por nombre" @input="sincronizarPorNombre(index)" />
                  <select v-model="material.producto_base" @change="sincronizarCodigo(index)">
                    <option :value="null" disabled>Seleccione un producto</option>
                    <option v-for="prod in productosDisponibles" :key="prod.id" :value="prod.id">
                      {{ prod.codigo }} - {{ prod.nombre }}
                    </option>
                  </select>
                  <input type="text" v-model="material.codigoDigitado" placeholder="Ingrese código del material" @input="sincronizarSelector(index)" />
                </td>
                <td>
                  <input v-model.number="material.cantidad" type="number" step="0.01" min="0.01" required @input="actualizarPesoMaterial(index)" />
                </td>
                <td>{{ material.peso_unitario }}</td>
                <td>{{ material.peso_total }}</td>
                <td>
                  <button @click.prevent="eliminarMaterial(index)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="materiales-actions">
          <button @click.prevent="agregarMaterial">Agregar Material</button>
          <button @click.prevent="guardarMateriales">Guardar Materiales</button>
        </div>
      </section>
  
      <!-- Consulta de Productos -->
      <section class="consulta-productos">
        <h2>Consulta de Productos Creados</h2>
        <div class="filters">
          <div class="filter-group">
            <label for="buscarCodigo">Buscar por Código:</label>
            <input v-model="filtroCodigo" id="buscarCodigo" placeholder="Ingrese código de producto" />
          </div>
          <div class="filter-group">
            <label for="buscarNombre">Buscar por Nombre:</label>
            <input v-model="filtroNombre" id="buscarNombre" placeholder="Ingrese nombre o parte del nombre" />
          </div>
          <div class="filter-group">
            <label for="limit">Mostrar:</label>
            <select v-model="limit" id="limit" @change="consultarProductos">
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="0">Todos</option>
            </select>
            <span> productos</span>
          </div>
          <div class="filter-actions">
            <button @click="consultarProductos">Consultar Productos</button>
            <button @click="limpiarCampos" class="btn-warning">Limpiar Campos</button>
            <button @click="exportarAExcel" class="btn-export">Exportar a Excel</button>
          </div>
        </div>
        <div v-if="productos.length" class="table-container">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Peso Total (g)</th>
                <th>Peso Unidad (g)</th>
                <th>Código de Barras</th>
                <th>Prod. Compuesto</th>
                <th>Stock Mínimo</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="prod in productos" :key="prod.id">
                <td>{{ prod.codigo }}</td>
                <td>{{ prod.nombre }}</td>
                <td>{{ prod.peso_total_gr }}</td>
                <td>{{ prod.peso_unidad_gr }}</td>
                <td>{{ prod.codigo_barras }}</td>
                <td>{{ prod.es_producto_compuesto ? 'Sí' : 'No' }}</td>
                <td>{{ prod.stock_minimo !== null ? prod.stock_minimo : '-' }}</td>
                <td>
                  <button @click="editarProducto(prod)">Editar</button>
                  <button @click="eliminarProducto(prod.id)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
          <button v-if="productos.length < totalProductos" @click="cargarMasProductos">Cargar más productos</button>
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
  name: 'GestionProductosMateriales',
  setup() {
    const store = useStore();
    const router = useRouter();

    // Referencias
    const producto = ref({ id: null, codigo: '', nombre: '', es_producto_compuesto: false, stock_minimo: null });
    const productos = ref([]);
    const materiales = ref([]);
    const productosDisponibles = ref([]);
    const modoEdicion = ref(false);
    const filtroCodigo = ref('');
    const filtroNombre = ref('');
    const totalProductos = ref(0);
    const offset = ref(0);
    const limit = ref(50);
    const archivoCsv = ref(null);
    const archivoActualizarCsv = ref(null);
    const erroresCsv = ref('');
    const erroresActualizarCsv = ref('');
    const mostrarModal = ref(false);
    const mostrarModalActualizar = ref(false);
    const isLoadingCarga = ref(false);
    const isLoadingActualizar = ref(false);
    const inputCsv = ref(null);
    const inputActualizarCsv = ref(null);

    const crearProducto = async () => {
      try {
        const payload = { ...producto.value };
        if (payload.es_producto_compuesto) {
          delete payload.peso_total_gr;
          delete payload.peso_unidad_gr;
        }
        const response = await axios.post('/inventory/productos', payload);
        producto.value.id = response.data.id;
        alert('Producto creado correctamente');
        resetearFormulario();
        consultarProductos();
      } catch (error) {
        console.error('Error al crear producto:', error);
        alert(error.response?.data?.error || 'Error al crear producto');
      }
    };

    const consultarProductos = async () => {
      try {
        const limiteConsulta = limit.value === 0 ? 10000 : limit.value;
        const params = {
          offset: offset.value,
          limit: limiteConsulta,
          search_codigo: filtroCodigo.value || '',
          search_nombre: filtroNombre.value || ''
        };
        const response = await axios.get('/inventory/productos', { params });
        productos.value = response.data.productos.sort((a, b) => a.codigo.localeCompare(b.codigo));
        totalProductos.value = response.data.total;
      } catch (error) {
        console.error('Error al cargar productos:', error);
        alert('Ocurrió un error al consultar los productos.');
      }
    };

    const cargarMaterialesProducto = async () => {
      if (!producto.value.id || !producto.value.es_producto_compuesto) return;
      try {
        const response = await axios.get(`/inventory/materiales-producto/${producto.value.id}`);
        materiales.value = response.data.materiales.map(material => {
          const productoBase = productosDisponibles.value.find(p => p.id === material.producto_base_id);
          return {
            id: material.id,
            producto_base: material.producto_base_id,
            codigoDigitado: productoBase ? productoBase.codigo : '',
            nombreDigitado: productoBase ? productoBase.nombre : '',
            cantidad: material.cantidad,
            peso_unitario: productoBase ? productoBase.peso_unidad_gr : 0,
            peso_total: material.cantidad * (productoBase ? productoBase.peso_unidad_gr : 0)
          };
        });
      } catch (error) {
        console.error('Error al cargar materiales:', error);
        alert('No se pudieron cargar los materiales del producto compuesto.');
      }
    };

    const cargarProductosDisponibles = async () => {
      try {
        const response = await axios.get('/inventory/productos', { params: { limit: 500 } });
        productosDisponibles.value = response.data.productos.sort((a, b) => a.codigo.localeCompare(b.codigo));
      } catch (error) {
        console.error('Error al cargar productos disponibles:', error);
        if (error.response?.status === 401) {
          router.push('/login');
        } else {
          alert('No se pudieron cargar los productos disponibles.');
        }
      }
    };

    const guardarMateriales = async () => {
      try {
        if (materiales.value.some(m => !m.producto_base || isNaN(m.cantidad) || m.cantidad <= 0)) {
          alert('Todos los materiales deben tener un producto base seleccionado y una cantidad válida mayor a 0.');
          return;
        }
        const payload = {
          producto_compuesto_id: producto.value.id,
          materiales: materiales.value.map(m => ({
            producto_base_id: m.producto_base,
            cantidad: Number(m.cantidad)
          }))
        };
        await axios.post('/inventory/materiales-producto', payload);
        alert('Materiales guardados correctamente');
        cargarMaterialesProducto();
      } catch (error) {
        console.error('Error al guardar materiales:', error);
        alert('Hubo un problema guardando los materiales.');
      }
    };

    const cargarMasProductos = async () => {
      try {
        offset.value += limit.value;
        const response = await axios.get('/inventory/productos', {
          params: { offset: offset.value, limit: limit.value }
        });
        productos.value = [...productos.value, ...response.data.productos.sort((a, b) => a.codigo.localeCompare(b.codigo))];
      } catch (error) {
        console.error('Error al cargar más productos:', error);
      }
    };

    const cargarCsv = (event) => {
      archivoCsv.value = event.target.files[0];
      erroresCsv.value = '';
    };

    const procesarCsv = async () => {
      if (!archivoCsv.value) {
        alert('Por favor, selecciona un archivo CSV.');
        return;
      }
      isLoadingCarga.value = true;
      try {
        const formData = new FormData();
        formData.append('file', archivoCsv.value);
        const response = await axios.post('/inventory/productos/csv', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        });
        const { message, productos_creados, productos_duplicados, errores } = response.data;
        let mensaje = `${message}\n\n`;
        if (productos_creados.length) mensaje += `✔ Productos creados: ${productos_creados.join(', ')}\n`;
        if (productos_duplicados.length) mensaje += `⚠️ Productos duplicados: ${productos_duplicados.join(', ')}\n`;
        if (errores.length) mensaje += `🛑 Errores detectados:\n- ${errores.join('\n- ')}\n`;
        alert(mensaje);
        erroresCsv.value = errores.length || productos_duplicados.length
          ? `⚠️ Reporte de errores:\n\n${productos_duplicados.length ? `🔹 Productos duplicados:\n- ${productos_duplicados.join('\n- ')}\n\n` : ''}${errores.length ? `🛑 Errores:\n- ${errores.join('\n- ')}\n` : ''}`
          : '';
        consultarProductos();
        limpiarSesionCsv();
      } catch (error) {
        console.error('Error al cargar archivo CSV:', error);
        let mensajeError = '❌ Error al cargar el archivo CSV.';
        if (error.code === 'ECONNABORTED') {
          mensajeError += ' La solicitud tardó demasiado. Intenta con un archivo más pequeño.';
        } else if (error.response) {
          mensajeError += ` Detalles: ${error.response.data.error || 'Error desconocido'}`;
        }
        alert(mensajeError);
      } finally {
        isLoadingCarga.value = false;
      }
    };

    const cargarArchivoActualizarCsv = (event) => {
      archivoActualizarCsv.value = event.target.files[0];
      erroresActualizarCsv.value = '';
    };

    const procesarActualizacionCsv = async () => {
      if (!archivoActualizarCsv.value) {
        alert('Por favor, selecciona un archivo CSV para actualizar.');
        return;
      }
      isLoadingActualizar.value = true;
      try {
        const formData = new FormData();
        formData.append('file', archivoActualizarCsv.value);
        const response = await axios.post('/inventory/productos/actualizar-csv', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        });
        const { message, productos_actualizados, productos_no_encontrados, errores } = response.data;
        let mensaje = `✅ ${message}\n\n`;
        if (productos_actualizados.length) {
          mensaje += `✔ Productos actualizados: ${productos_actualizados.join(', ')}\n`;
        }
        if (productos_no_encontrados.length) {
          mensaje += `⚠️ Productos no encontrados: ${productos_no_encontrados.join(', ')}\n`;
        }
        if (errores.length) {
          mensaje += `🛑 Errores detectados:\n- ${errores.join('\n- ')}\n`;
        }
        alert(mensaje);
        erroresActualizarCsv.value = errores.length || productos_no_encontrados.length
          ? `⚠️ Reporte de errores:\n\n${productos_no_encontrados.length ? `🔹 Productos no encontrados:\n- ${productos_no_encontrados.join('\n- ')}\n\n` : ''}${errores.length ? `🛑 Errores:\n- ${errores.join('\n- ')}\n` : ''}`
          : '';
        consultarProductos();
        limpiarActualizarCsv();
      } catch (error) {
        console.error('Error al actualizar productos desde CSV:', error);
        let mensajeError = '❌ Error al actualizar productos desde CSV.';
        if (error.code === 'ECONNABORTED') {
          mensajeError += ' La solicitud tardó demasiado. Intenta con un archivo más pequeño.';
        } else if (error.response) {
          mensajeError += ` Detalles: ${error.response.data.error || 'Error desconocido'}`;
        }
        alert(mensajeError);
      } finally {
        isLoadingActualizar.value = false;
      }
    };

    const sincronizarSelector = (index) => {
      const material = materiales.value[index];
      const productoEncontrado = productosDisponibles.value.find(p => p.codigo === material.codigoDigitado);
      if (productoEncontrado) {
        material.producto_base = productoEncontrado.id;
        material.nombreDigitado = productoEncontrado.nombre;
        actualizarPesoMaterial(index);
      }
    };

    const sincronizarCodigo = (index) => {
      const material = materiales.value[index];
      const productoEncontrado = productosDisponibles.value.find(p => p.id === material.producto_base);
      if (productoEncontrado) {
        material.codigoDigitado = productoEncontrado.codigo;
        material.nombreDigitado = productoEncontrado.nombre;
        actualizarPesoMaterial(index);
      }
    };

    const sincronizarPorNombre = (index) => {
      const material = materiales.value[index];
      if (!material.nombreDigitado) return;
      const productoEncontrado = productosDisponibles.value.find(p => p.nombre.toLowerCase().includes(material.nombreDigitado.toLowerCase()));
      if (productoEncontrado) {
        material.producto_base = productoEncontrado.id;
        material.codigoDigitado = productoEncontrado.codigo;
        actualizarPesoMaterial(index);
      } else {
        material.producto_base = null;
      }
    };

    const editarProducto = (prod) => {
      modoEdicion.value = true;
      producto.value = { ...prod };
      cargarProductosDisponibles().then(() => cargarMaterialesProducto());
    };

    const actualizarProducto = async () => {
      try {
        await axios.put(`/inventory/productos/${producto.value.id}`, producto.value);
        alert('Producto actualizado correctamente');
        consultarProductos();
        cancelarEdicion();
      } catch (error) {
        console.error('Error al actualizar producto:', error);
        alert('Error al actualizar producto');
      }
    };

    const cancelarEdicion = () => {
      modoEdicion.value = false;
      resetearFormulario();
      consultarProductos();
    };

    const resetearFormulario = () => {
      producto.value = { id: null, codigo: '', nombre: '', es_producto_compuesto: false, peso_total_gr: '', peso_unidad_gr: '', codigo_barras: '', stock_minimo: null };
      materiales.value = [];
    };

    const agregarMaterial = () => {
      materiales.value.push({ producto_base: null, cantidad: 1, peso_unitario: 0, peso_total: 0, codigoDigitado: '', nombreDigitado: '' });
    };

    const eliminarMaterial = async (index) => {
      const material = materiales.value[index];
      if (material.id) {
        try {
          await axios.delete(`/inventory/materiales-producto/${material.id}`);
          alert('Material eliminado correctamente.');
        } catch (error) {
          console.error('Error al eliminar material:', error);
          alert('No se pudo eliminar el material.');
        }
      }
      materiales.value.splice(index, 1);
    };

    const actualizarPesoMaterial = (index) => {
      const material = materiales.value[index];
      const producto = productosDisponibles.value.find(p => p.id === material.producto_base);
      if (producto) {
        material.peso_unitario = producto.peso_unidad_gr;
        material.peso_total = material.cantidad * material.peso_unitario;
      } else {
        material.peso_unitario = 0;
        material.peso_total = 0;
      }
    };

    const eliminarProducto = async (productoId) => {
      if (confirm('¿Estás seguro de que deseas eliminar este producto?')) {
        try {
          await axios.delete(`/inventory/productos/${productoId}`);
          alert('Producto eliminado correctamente');
          productos.value = productos.value.filter(prod => prod.id !== productoId);
          totalProductos.value -= 1;
        } catch (error) {
          console.error('Error al eliminar producto:', error);
          alert('No se pudo eliminar el producto.');
        }
      }
    };

    const exportarAExcel = async () => {
      try {
        const response = await axios.get('/inventory/productos', {
          params: { offset: 0, limit: 10000, search_codigo: filtroCodigo.value, search_nombre: filtroNombre.value }
        });
        const productosTodos = response.data.productos;
        const worksheetData = [
          ['Productos Cargados'],
          ['Código', 'Nombre', 'Peso Total (g)', 'Peso Unidad (g)', 'Código de Barras', 'Prod. Compuesto', 'Stock Mínimo'],
          ...productosTodos.map(prod => [
            prod.codigo,
            prod.nombre,
            prod.peso_total_gr || '',
            prod.peso_unidad_gr || '',
            prod.codigo_barras || '',
            prod.es_producto_compuesto ? 'Sí' : 'No',
            prod.stock_minimo !== null ? prod.stock_minimo : ''
          ])
        ];
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Productos');
        XLSX.writeFile(workbook, `Productos_Cargados_${new Date().toISOString().slice(0, 10)}.xlsx`);
      } catch (error) {
        console.error('Error al exportar a Excel:', error);
        alert('Ocurrió un error al exportar los productos a Excel.');
      }
    };

    const copiarErrores = () => {
      navigator.clipboard.writeText(erroresCsv.value).then(() => alert('Errores copiados al portapapeles.'));
    };

    const copiarErroresActualizar = () => {
      navigator.clipboard.writeText(erroresActualizarCsv.value).then(() => alert('Errores copiados al portapapeles.'));
    };

    const limpiarPagina = () => {
      resetearFormulario();
      productos.value = [];
      filtroCodigo.value = '';
      filtroNombre.value = '';
      totalProductos.value = 0;
      offset.value = 0;
      limpiarSesionCsv();
      limpiarActualizarCsv();
    };

    const limpiarCampos = () => {
      filtroCodigo.value = '';
      filtroNombre.value = '';
      productos.value = [];
      totalProductos.value = 0;
      offset.value = 0;
    };

    const limpiarSesionCsv = () => {
      archivoCsv.value = null;
      erroresCsv.value = '';
      if (inputCsv.value) inputCsv.value.value = '';
    };

    const limpiarActualizarCsv = () => {
      archivoActualizarCsv.value = null;
      erroresActualizarCsv.value = '';
      if (inputActualizarCsv.value) inputActualizarCsv.value.value = '';
    };

    const limpiarSesion = () => {
      resetearFormulario();
      modoEdicion.value = false;
    };

    const descargarPlantillaCSV = () => {
      const csvContent = `# Instructivo: Llene los campos según corresponda.\n` +
        `# Si "es_producto_compuesto" es "Sí", debe completar las columnas de "cantidad_productos", "codigo1", "cantidad1", "codigo2", etc.\n` +
        `# Si el producto es Base, se coloca cero 0. Si el producto es compuesto, indicar cuántos productos base lo conforman.\n` +
        `# "stock_minimo" es opcional; déjelo en blanco si no aplica.\n` +
        `codigo,nombre,peso_total_gr,peso_unidad_gr,codigo_barras,es_producto_compuesto,stock_minimo,cantidad_productos,codigo1,cantidad1,codigo2,cantidad2\n` +
        `GRA12345678901234,Ejemplo Producto Base,500,50,1234567890123,No,100,0,,,,\n` +
        `GRA98765432109876,Ejemplo Producto Compuesto,,,9876543210987,Sí,10,2,GRA12345678901234,2,GRA12199905000000,3\n`;
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', 'Plantilla_Carga_Productos.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const descargarPlantillaActualizarCSV = () => {
      const csvContent = `# Instructivo: Llene los campos para actualizar productos existentes.\n` +
        `# 'codigo' es obligatorio y debe coincidir con un producto existente.\n` +
        `# Los demás campos son opcionales; déjelos en blanco para no modificarlos.\n` +
        `# Si 'es_producto_compuesto' es "Sí", complete 'cantidad_productos', 'codigo1', 'cantidad1', etc.\n` +
        `# Los productos base deben existir.\n` +
        `# Nota: El código y el nombre deben ser únicos.\n` +
        `codigo,nombre,peso_total_gr,peso_unidad_gr,codigo_barras,es_producto_compuesto,stock_minimo,cantidad_productos,codigo1,cantidad1,codigo2,cantidad2\n` +
        `GRA12345678901234,Producto Base Actualizado,600,60,1234567890123,No,150,,,,\n` +
        `GRA98765432109876,Kit Compuesto Actualizado,,,9876543210987,Sí,20,2,GRA12345678901234,3,GRA12199905000000,4\n`;
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', 'Plantilla_Actualizacion_Productos.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };


    const mostrarInstructivo = () => {
      mostrarModal.value = true;
    };

    const cerrarModal = () => {
      mostrarModal.value = false;
    };

    const mostrarInstructivoActualizar = () => {
      mostrarModalActualizar.value = true;
    };

    const cerrarModalActualizar = () => {
      mostrarModalActualizar.value = false;
    };

    cargarProductosDisponibles();

    return {
      producto,
      productos,
      materiales,
      productosDisponibles,
      modoEdicion,
      filtroCodigo,
      filtroNombre,
      totalProductos,
      offset,
      limit,
      archivoCsv,
      archivoActualizarCsv,
      erroresCsv,
      erroresActualizarCsv,
      mostrarModal,
      mostrarModalActualizar,
      isLoadingCarga,
      isLoadingActualizar,
      inputCsv,
      inputActualizarCsv,
      crearProducto,
      consultarProductos,
      cargarMaterialesProducto,
      cargarProductosDisponibles,
      guardarMateriales,
      cargarMasProductos,
      cargarCsv,
      procesarCsv,
      cargarArchivoActualizarCsv,
      procesarActualizacionCsv,
      sincronizarSelector,
      sincronizarCodigo,
      sincronizarPorNombre,
      editarProducto,
      actualizarProducto,
      cancelarEdicion,
      resetearFormulario,
      agregarMaterial,
      eliminarMaterial,
      actualizarPesoMaterial,
      eliminarProducto,
      exportarAExcel,
      copiarErrores,
      copiarErroresActualizar,
      limpiarPagina,
      limpiarCampos,
      limpiarSesionCsv,
      limpiarActualizarCsv,
      limpiarSesion,
      descargarPlantillaCSV,
      descargarPlantillaActualizarCSV,
      mostrarInstructivo,
      cerrarModal,
      mostrarInstructivoActualizar,
      cerrarModalActualizar
    };
  },
  watch: {
    'producto.id': function(newVal) {
      if (newVal) this.cargarMaterialesProducto();
    }
  }
};
</script>
  
<style scoped>
.gestion-productos-materiales {
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

.top-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  justify-content: flex-end;
}

button, .btn {
  padding: 8px 16px;
  background-color: #42b983; /* Verde característico */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

button:hover, .btn:hover {
  background-color: #2c3e50; /* Hover oscuro */
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-warning {
  background-color: #ffc107; /* Amarillo para "limpiar" */
  color: #333;
}

.btn-warning:hover {
  background-color: #e0a800;
}

.btn-export {
  background-color: #28a745; /* Verde más oscuro para exportar */
}

.btn-export:hover {
  background-color: #218838;
}

.btn-cerrar {
  background-color: #dc3545; /* Rojo para cerrar modal */
}

.btn-cerrar:hover {
  background-color: #c82333;
}

.carga-csv, .form-section, .materiales-section, .consulta-productos {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 30px;
}

.carga-input {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.carga-input input[type="file"] {
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.carga-links {
  display: flex;
  gap: 20px;
}

.link-descarga, .link-instructivo {
  color: #42b983; /* Verde para enlaces */
  text-decoration: none;
  cursor: pointer;
}

.link-descarga:hover, .link-instructivo:hover {
  color: #2c3e50;
  text-decoration: underline;
}

.error-container {
  margin-top: 15px;
}

.error-container textarea {
  width: 100%;
  height: 100px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  resize: none;
  font-size: 14px;
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
  margin-top: 20px;
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

th, td {
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

.materiales-actions {
  margin-top: 20px;
  display: flex;
  gap: 15px;
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
}

.filter-group label {
  font-weight: bold;
  margin-bottom: 5px;
}

.filter-group input, .filter-group select {
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.filter-actions {
  display: flex;
  gap: 15px;
  align-items: flex-end;
}

.modal-instructivo {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-contenido {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
}

.spinner-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>