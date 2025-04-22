<template>
  <div class="accumulated-sales-by-pdv">
    <h1>
      Venta Acumulada por PDV a: {{ months[month - 1].name }}
      <span v-if="endDate">{{ endDate.split('-')[2] }}</span>
      {{ year }}
    </h1>
    <div class="filters">
      <label>Año:</label>
      <select v-model="year" @change="updateEndDateOptions; fetchData">
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </select>
      <label>Mes:</label>
      <select v-model="month" @change="updateEndDateOptions; fetchData">
        <option v-for="m in months" :key="m.num" :value="m.num">{{ m.name }}</option>
      </select>
      <label>Día Final:</label>
      <select v-model="endDate" @change="fetchData">
        <option v-for="day in availableDays" :key="day" :value="day">{{ day.split('-')[2] }}</option>
      </select>
      <label>Estatus PDV:</label>
      <select v-model="status" @change="fetchPDVs">
        <option value="Todos">Todos</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <label>Punto de Venta:</label>
      <select v-model="pdv" @change="fetchData">
        <option v-for="p in pdvs" :key="p" :value="p">{{ p }}</option>
      </select>
    </div>

    <!-- Botones para exportar -->
    <div class="sort-buttons">
      <button @click="exportToExcel" :disabled="noData">Exportar a Excel</button>
      <button @click="exportToPDF" :disabled="noData">Exportar a PDF</button>
    </div>

    <!-- Mensaje si no hay datos -->
    <div v-if="noData" class="no-data-message">
      No hay datos disponibles para el mes, año y PDV seleccionados.
    </div>

    <!-- Tabla de Métricas -->
    <div v-else class="table-container">
      <table class="sales-table">
        <thead>
          <tr>
            <th>Métrica</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Venta Acumulada</td>
            <td>{{ formatCurrency(data.venta_acumulada) }}</td>
          </tr>
          <tr>
            <td>Venta Proyectada</td>
            <td>{{ formatCurrency(data.venta_proyectada) }}</td>
          </tr>
          <tr>
            <td>Presupuesto</td>
            <td>{{ formatCurrency(data.presupuesto) }}</td>
          </tr>
          <tr>
            <td>Cumplimiento a la Fecha</td>
            <td>{{ formatCurrency(data.cumplimiento_a_la_fecha) }}</td>
          </tr>
          <tr>
            <td>% Cumplimiento</td>
            <td>{{ data.cumplimiento_porcentual }}% {{ data.cumplimiento_icono }}</td>
          </tr>
          <tr>
            <td>Saldo para Cumplir</td>
            <td :class="data.saldo_para_cumplir >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(data.saldo_para_cumplir) }}
            </td>
          </tr>
          <tr>
            <td>Venta mes {{ months[month - 1].name }} del Año Anterior</td>
            <td>{{ formatCurrency(data.venta_ano_anterior) }}</td>
          </tr>
          <tr>
            <td>Crecimiento (%)</td>
            <td :class="data.crecimiento_porcentual >= 0 ? 'positive' : 'negative'">
              {{ data.crecimiento_porcentual }}%
            </td>
          </tr>
          <tr>
            <td>Crecimiento ($)</td>
            <td :class="data.crecimiento_valor >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(data.crecimiento_valor) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Gráficos -->
    <div v-if="!noData" class="charts-container">
      <!-- Gráficos de Productos (uno al lado del otro) -->
      <div class="chart-row">
        <div class="chart-wrapper">
          <h2>Top 5 Productos Más Vendidos</h2>
          <Bar :data="productChartData" :options="productChartOptions" />
        </div>
        <div class="chart-wrapper">
          <h2>Distribución de Ventas (Top 5 Productos)</h2>
          <Doughnut :data="productDoughnutChartData" :options="doughnutChartOptions" />
        </div>
      </div>

      <!-- Gráficos de Asesores (uno al lado del otro) -->
      <div class="chart-row">
        <div class="chart-wrapper">
          <h2>Top 5 Asesores con más ventas</h2>
          <Bar :data="sellerChartData" :options="sellerChartOptions" />
        </div>
        <div class="chart-wrapper">
          <h2>Distribución de Ventas (Top 5 Asesores)</h2>
          <Doughnut :data="sellerDoughnutChartData" :options="doughnutChartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from '@/api/axios';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { Bar, Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels'; // Importar el plugin
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

// Registrar los componentes de Chart.js y el plugin
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement, ChartDataLabels);   // quitamos (, ChartDataLabels ) del parentesis para que no se muestre de manera grlobal en todas las paginas

export default {
  name: 'AccumulatedSalesByPDV',
  components: {
    Bar,
    Doughnut,
  },
  setup() {
    // Datos reactivos
    const store = useStore();
    const router = useRouter();
    const year = ref(null);
    const years = ref([]);
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1;
    const month = ref(currentMonth);
    const months = ref([
      { num: 1, name: 'Enero' },
      { num: 2, name: 'Febrero' },
      { num: 3, name: 'Marzo' },
      { num: 4, name: 'Abril' },
      { num: 5, name: 'Mayo' },
      { num: 6, name: 'Junio' },
      { num: 7, name: 'Julio' },
      { num: 8, name: 'Agosto' },
      { num: 9, name: 'Septiembre' },
      { num: 10, name: 'Octubre' },
      { num: 11, name: 'Noviembre' },
      { num: 12, name: 'Diciembre' },
    ]);
    const status = ref('Activo');
    const pdv = ref('');
    const pdvs = ref([]);
    const endDate = ref('');
    const availableDays = ref([]);
    const data = ref(null);

    // Computed para determinar si no hay datos
    const noData = computed(() => {
      return !data.value || (data.value.venta_acumulada === 0 && data.value.venta_proyectada === 0);
    });

    // Computed para los datos del gráfico de barras de productos
    const productChartData = computed(() => {
      if (!data.value || !data.value.top_products) return { labels: [], datasets: [] };

      const labels = data.value.top_products.map(item => item.product);
      const values = data.value.top_products.map(item => item.sales);

      return {
        labels: labels,
        datasets: [
          {
            label: 'Ventas (COP)',
            data: values,
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
          },
        ],
      };
    });

    const productChartOptions = {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Ventas (COP)',
          },
          ticks: {
            callback: function (value) {
              return new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
              }).format(value);
            },
          },
        },
        y: {
          title: {
            display: true,
            text: 'Producto',
          },
          ticks: {
            font: {
              size: 10,
            },
            padding: 10,
            maxRotation: 45,
            minRotation: 0,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              label += new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
              }).format(context.parsed.x);
              return label;
            },
          },
        },
        datalabels: {
          anchor: 'center', // Posicionar la etiqueta en el centro de la barra
          align: 'center', // Alinear el texto al centro
          color: '#fff', // Color del texto (blanco para que contraste con el fondo de la barra)
          font: {
            size: 10,
            weight: 'bold',
          },
          formatter: function (value) {
            return new Intl.NumberFormat('es-CO', {
              style: 'currency',
              currency: 'COP',
              minimumFractionDigits: 0,
            }).format(value);
          },
        },
      },
    };

    // Computed para el gráfico de dona de productos
    const productDoughnutChartData = computed(() => {
      if (!data.value || !data.value.top_products) return { labels: [], datasets: [] };

      const colors = [
        'rgba(255, 99, 132, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(153, 102, 255, 0.6)',
      ];
      const borderColors = colors.map(color => color.replace('0.6', '1'));

      return {
        labels: data.value.top_products.map(item => item.product),
        datasets: [
          {
            label: 'Distribución de Ventas',
            data: data.value.top_products.map(item => item.sales),
            backgroundColor: colors,
            borderColor: borderColors,
            borderWidth: 1,
          },
        ],
      };
    });

    // Computed para los datos del gráfico de barras de asesores
    const sellerChartData = computed(() => {
      if (!data.value || !data.value.top_sellers) return { labels: [], datasets: [] };

      const labels = data.value.top_sellers.map(item => item.seller);
      const values = data.value.top_sellers.map(item => item.sales);

      return {
        labels: labels,
        datasets: [
          {
            label: 'Ventas (COP)',
            data: values,
            backgroundColor: 'rgba(255, 159, 64, 0.6)',
            borderColor: 'rgba(255, 159, 64, 1)',
            borderWidth: 1,
          },
        ],
      };
    });

    const sellerChartOptions = {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Ventas (COP)',
          },
          ticks: {
            callback: function (value) {
              return new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
              }).format(value);
            },
          },
        },
        y: {
          title: {
            display: true,
            text: 'Asesor',
          },
          ticks: {
            font: {
              size: 10,
            },
            padding: 10,
            maxRotation: 45,
            minRotation: 0,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              label += new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
              }).format(context.parsed.x);
              return label;
            },
          },
        },
        datalabels: {
          anchor: 'center', // Posicionar la etiqueta en el centro de la barra
          align: 'center', // Alinear el texto al centro
          color: '#fff', // Color del texto (blanco para que contraste con el fondo de la barra)
          font: {
            size: 10,
            weight: 'bold',
          },
          formatter: function (value) {
            return new Intl.NumberFormat('es-CO', {
              style: 'currency',
              currency: 'COP',
              minimumFractionDigits: 0,
            }).format(value);
          },
        },
      },
    };

    // Computed para el gráfico de dona de asesores
    const sellerDoughnutChartData = computed(() => {
      if (!data.value || !data.value.top_sellers) return { labels: [], datasets: [] };

      const colors = [
        'rgba(255, 99, 132, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(153, 102, 255, 0.6)',
      ];
      const borderColors = colors.map(color => color.replace('0.6', '1'));

      return {
        labels: data.value.top_sellers.map(item => item.seller),
        datasets: [
          {
            label: 'Distribución de Ventas',
            data: data.value.top_sellers.map(item => item.sales),
            backgroundColor: colors,
            borderColor: borderColors,
            borderWidth: 1,
          },
        ],
      };
    });

    const doughnutChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'right',
          labels: {
            boxWidth: 20,
            padding: 10,
            font: {
              size: 10,
            },
            generateLabels: function (chart) {
              const data = chart.data;
              if (data.labels.length && data.datasets.length) {
                return data.labels.map((label, i) => {
                  const maxLength = 15;
                  let text = label;
                  if (label.length > maxLength) {
                    const words = label.split(' ');
                    let line = '';
                    const lines = [];
                    for (const word of words) {
                      if ((line + word).length > maxLength) {
                        lines.push(line.trim());
                        line = word + ' ';
                      } else {
                        line += word + ' ';
                      }
                    }
                    if (line) lines.push(line.trim());
                    text = lines.join('\n');
                  }
                  return {
                    text: text,
                    fillStyle: data.datasets[0].backgroundColor[i],
                    hidden: isNaN(data.datasets[0].data[i]) || chart.getDatasetMeta(0).data[i].hidden,
                    index: i,
                  };
                });
              }
              return [];
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.label || '';
              if (label) {
                label += ': ';
              }
              label += new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
              }).format(context.parsed);
              return label;
            },
          },
        },
        datalabels: {
          display: false, // Desactivar datalabels para los gráficos de dona
        },
      },
    };

    // Obtener los años disponibles
    const fetchAvailableYears = async () => {
      try {
        const response = await axios.get('/available-years');
        years.value = response.data.years || [];
        if (years.value.length > 0) {
          year.value = years.value.includes(currentYear) ? currentYear : years.value[0];
          updateEndDateOptions();
          fetchPDVs();
        }
      } catch (error) {
        console.error('Error fetching available years:', error);
        years.value = Array.from({ length: 5 }, (_, i) => currentYear + i - 2);
        year.value = currentYear;
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en available-years, redirigiendo al login');
          router.push('/login');
        } else {
          updateEndDateOptions();
          fetchPDVs();
        }
      }
    };

    // Obtener los PDVs disponibles con filtro de estatus
    const fetchPDVs = async () => {
      try {
        const response = await axios.get('/dashboard/historical_sales', {
          params: { status: status.value },
        });
        pdvs.value = response.data.data
          .filter(row => row.pdv !== 'Total')
          .map(row => row.pdv);
        pdv.value = pdvs.value[0] || '';
        fetchData();
      } catch (error) {
        console.error('Error fetching PDVs:', error);
        pdvs.value = [];
        pdv.value = '';
        if (error.response && error.response.status === 401) {
          console.log('No autorizado en historical_sales, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Actualizar las opciones de fecha final según el año y mes seleccionados
    const updateEndDateOptions = () => {
      if (!year.value || !month.value) return;

      const daysInMonth = new Date(year.value, month.value, 0).getDate();
      availableDays.value = Array.from({ length: daysInMonth }, (_, i) => {
        const day = i + 1;
        return `${year.value}-${String(month.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      });

      const today = new Date();
      if (year.value === today.getFullYear() && month.value === today.getMonth() + 1) {
        const todayStr = `${year.value}-${String(month.value).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        endDate.value = availableDays.value.includes(todayStr) ? todayStr : availableDays.value[availableDays.value.length - 1];
      } else {
        endDate.value = availableDays.value[availableDays.value.length - 1];
      }

      fetchData();
    };

    // Obtener los datos del dashboard
    const fetchData = async () => {
      if (!year.value || !month.value || !pdv.value || !endDate.value) return;

      const [endYear, endMonth] = endDate.value.split('-').map(Number);
      if (endYear !== year.value || endMonth !== month.value) {
        console.warn('endDate does not match selected year and month, updating endDate...');
        updateEndDateOptions();
        return;
      }

      try {
        const response = await axios.get('/dashboard/accumulated-sales-by-pdv', {
          params: {
            year: year.value,
            month: month.value,
            pdv: pdv.value,
            end_date: endDate.value,
            status: status.value,
          },
        });
        data.value = response.data;
      } catch (error) {
        console.error('Error fetching accumulated sales data:', error);
        data.value = null;
        if (error.response && error.response.status === 401) {
          console.log('No autorizado, redirigiendo al login');
          router.push('/login');
        }
      }
    };

    // Formatear moneda
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
      }).format(value);
    };

    // Exportar a Excel
    const exportToExcel = () => {
      if (!data.value) return;

      const filtersData = [
        { Filtro: 'Año', Valor: year.value },
        { Filtro: 'Mes', Valor: months.value[month.value - 1].name },
        { Filtro: 'Punto de Venta (PDV)', Valor: pdv.value },
        { Filtro: 'Fecha Final', Valor: endDate.value },
        { Filtro: 'Estatus PDV', Valor: status.value },
      ];

      const tableData = [
        { Métrica: 'Venta Acumulada', Valor: data.value.venta_acumulada },
        { Métrica: 'Venta Proyectada', Valor: data.value.venta_proyectada },
        { Métrica: 'Presupuesto', Valor: data.value.presupuesto },
        { Métrica: 'Cumplimiento a la Fecha', Valor: data.value.cumplimiento_a_la_fecha },
        { Métrica: '% Cumplimiento', Valor: `${data.value.cumplimiento_porcentual}%` },
        { Métrica: 'Saldo para Cumplir', Valor: data.value.saldo_para_cumplir },
        { Métrica: `Venta mes ${months.value[month.value - 1].name} del Año Anterior`, Valor: data.value.venta_ano_anterior },
        { Métrica: 'Crecimiento (%)', Valor: `${data.value.crecimiento_porcentual}%` },
        { Métrica: 'Crecimiento ($)', Valor: data.value.crecimiento_valor },
      ];

      tableData.push({}, { Métrica: 'Top 5 Productos Más Vendidos', Valor: '' });
      data.value.top_products.forEach((item, index) => {
        tableData.push({ Métrica: `Producto ${index + 1}`, Valor: `${item.product}: ${formatCurrency(item.sales)}` });
      });

      tableData.push({}, { Métrica: 'Top 5 Asesores Más Vendidos', Valor: '' });
      data.value.top_sellers.forEach((item, index) => {
        tableData.push({ Métrica: `Asesor ${index + 1}`, Valor: `${item.seller}: ${formatCurrency(item.sales)}` });
      });

      const ws = XLSX.utils.json_to_sheet([]);
      XLSX.utils.sheet_add_json(ws, filtersData, { origin: 'A1', skipHeader: false });
      const filtersRowCount = filtersData.length;
      const emptyRow = filtersRowCount + 2;
      XLSX.utils.sheet_add_json(ws, tableData, { origin: `A${emptyRow}`, skipHeader: false });

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Venta Acumulada por PDV');
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([wbout], { type: 'application/octet-stream' });
      saveAs(blob, `Venta_Acumulada_${pdv.value}_${months.value[month.value - 1].name}_${year.value}.xlsx`);
    };

    // Exportar a PDF
    const exportToPDF = async () => {
      if (!data.value) return;

      const pdf = new jsPDF('p', 'mm', 'letter'); // Cambiar a formato Carta
      const pageWidth = pdf.internal.pageSize.getWidth(); // 215.9 mm
      const pageHeight = pdf.internal.pageSize.getHeight(); // 279.4 mm
      const margin = 10;
      let yPosition = margin;

      // Título
      pdf.setFontSize(16);
      pdf.text(`Venta Acumulada por PDV - ${pdv.value}`, margin, yPosition);
      yPosition += 10;

      // Filtros
      //pdf.setFontSize(12);
      //pdf.text('Filtros Aplicados:', margin, yPosition);
      //yPosition += 5;
      pdf.setFontSize(10);
      pdf.text(`Año: ${year.value}`, margin, yPosition);
      yPosition += 5;
      pdf.text(`Mes: ${months.value[month.value - 1].name}`, margin, yPosition);
      yPosition += 5;
      pdf.text(`Día Final: ${endDate.value.split('-')[2]}`, margin, yPosition);
      yPosition += 5;
      pdf.text(`Estatus PDV: ${status.value}`, margin, yPosition);
      yPosition += 5;
      pdf.text(`Punto de Venta: ${pdv.value}`, margin, yPosition);
      yPosition += 10;

      // Capturar la tabla de métricas como imagen
      const tableElement = document.querySelector('.table-container');
      const tableCanvas = await html2canvas(tableElement, { scale: 2 });
      const tableImgData = tableCanvas.toDataURL('image/png');
      const tableImgProps = pdf.getImageProperties(tableImgData);
      const tableWidth = 370; // Ajustar para el formato Carta (215.9 mm - 2 * 10 mm de margen)
      const tableHeight = (tableImgProps.height * tableWidth) / tableImgProps.width;
      const tableX = (pageWidth - tableWidth) / 2; // Centrar la tabla
      pdf.addImage(tableImgData, 'PNG', tableX, yPosition, tableWidth, tableHeight);
      yPosition += tableHeight + 10;

      // Verificar si necesitamos una nueva página
      if (yPosition + 100 > pageHeight) {
        pdf.addPage();
        yPosition = margin;
      }

      // Capturar los gráficos
      const chartRows = document.querySelectorAll('.chart-row');
      for (let i = 0; i < chartRows.length; i++) {
        const chartRow = chartRows[i];
        const chartWrappers = chartRow.querySelectorAll('.chart-wrapper');
        const chartImages = [];

        // Capturar cada gráfico en la fila con un retraso para asegurar el renderizado
        for (let j = 0; j < chartWrappers.length; j++) {
          await new Promise(resolve => setTimeout(resolve, 500));
          const chartCanvas = await html2canvas(chartWrappers[j], { scale: 2 });
          const chartImgData = chartCanvas.toDataURL('image/png');
          chartImages.push({ data: chartImgData, props: pdf.getImageProperties(chartImgData) });
        }

        // Añadir los gráficos al PDF
        const chartWidth = 97; // Ajustar para el formato Carta (215.9 mm - 2 * 10 mm de margen - 5 mm de espacio)
        const chartHeight = (chartImages[0].props.height * chartWidth) / chartImages[0].props.width * 1.2; // Aumentar el alto
        const xPositions = [margin, margin + chartWidth + 5]; // Ajustar posiciones

        for (let j = 0; j < chartImages.length; j++) {
          pdf.addImage(chartImages[j].data, 'PNG', xPositions[j], yPosition, chartWidth, chartHeight);
        }

        yPosition += chartHeight + 12;

        // Verificar si necesitamos una nueva página
        if (yPosition + 100 > pageHeight && i < chartRows.length - 1) {
          pdf.addPage();
          yPosition = margin;
        }
      }

      // Guardar el PDF
      pdf.save(`Venta_Acumulada_${pdv.value}_${months.value[month.value - 1].name}_${year.value}.pdf`);
    };

    // Cargar datos iniciales
    onMounted(() => {
      if (store.state.auth.token) {
        fetchAvailableYears();
      } else {
        console.log('No hay token, redirigiendo al login');
        router.push('/login');
      }
    });

    return {
      year,
      years,
      month,
      months,
      status,
      pdv,
      pdvs,
      endDate,
      availableDays,
      data,
      noData,
      productChartData,
      productChartOptions,
      productDoughnutChartData,
      sellerChartData,
      sellerChartOptions,
      sellerDoughnutChartData,
      doughnutChartOptions,
      fetchAvailableYears,
      fetchPDVs,
      updateEndDateOptions,
      fetchData,
      formatCurrency,
      exportToExcel,
      exportToPDF,
    };
  },
};
</script>

<style scoped>
.accumulated-sales-by-pdv {
  padding: 20px;
}

.filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters label {
  font-weight: bold;
}

.filters select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.sort-buttons {
  margin-bottom: 20px;
}

.sort-buttons button {
  margin-right: 10px;
  padding: 5px 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.sort-buttons button:hover {
  background-color: #2c3e50;
}

.sort-buttons button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
  display: flex;
  justify-content: center;
}

.sales-table {
  width: 600px;
  border-collapse: collapse;
  font-size: 18px; /* Aumentar para mejor legibilidad en el PDF */
}

.sales-table th,
.sales-table td {
  border: 1px solid #ddd;
  padding: 4px;
  text-align: center;
}

.sales-table th {
  background-color: #f2f2f2;
  font-size: 14px; /* Aumentar para los encabezados */
}

.sales-table td {
  max-width: 200px;
  white-space: normal;
  word-wrap: break-word;
}

.sales-table td:first-child {
  text-align: left;
}

.positive {
  color: green;
}

.negative {
  color: red;
}

.no-data-message {
  text-align: center;
  color: #888;
  margin: 20px 0;
  font-size: 14px;
}

.charts-container {
  margin-top: 40px;
}

.chart-row {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
}

.chart-wrapper {
  flex: 1;
  margin: 0 10px;
  height: 280px; /* Aumentar para asegurar que los gráficos se rendericen completamente */
  max-width: 600px;
}

.chart-wrapper h2 {
  text-align: center;
  margin-bottom: 5px;
  font-size: 16px;
  margin-top: 20px;
}
</style>