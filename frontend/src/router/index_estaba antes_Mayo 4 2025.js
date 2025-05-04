import { createRouter, createWebHashHistory } from 'vue-router';
import { useStore } from 'vuex';
import Login from '../views/Login.vue';
import MainMenu from '../views/MainMenu.vue';
import AnalysisMenu from '../views/AnalysisMenu.vue';
import Admin from '../views/Admin.vue';
import Clientes from '../views/Clientes.vue';
import Profiles from '../views/Profiles.vue';
import Users from '../views/Users.vue';
import UploadMenu from '../views/UploadMenu.vue';
import UploadSales from '../components/UploadSales.vue';
import UploadArqueo from '../components/UploadArqueo.vue';
import UploadVentaMensual from '../components/UploadVentaMensual.vue';
import UploadBudget from '../components/UploadBudget.vue';
import DashboardMenu from '../views/DashboardMenu.vue';
import HistoricalSales from '../views/HistoricalSales.vue';
import MonthlyPerformance from '../views/MonthlyPerformance.vue';
import DailySales from '../views/DailySales.vue';
import SalesByTimeSlot from '../views/SalesByTimeSlot.vue';
import SalesByPaymentMethod from '../views/SalesByPaymentMethod.vue';
import SalesByProduct from '../views/SalesByProduct.vue';
import SalesBySeller from '../views/SalesBySeller.vue';
import AccumulatedSalesByPDV from '../views/AccumulatedSalesByPDV.vue';
import PointsOfSale from '../views/PointsOfSale.vue';
import ProfilesClientes from '../views/ProfilesClientes.vue';
import UsersClientes from '../views/UsersClientes.vue';
import CutoffConfig from '../views/CutoffConfig.vue';


const routes = [
  {
    path: '/',
    name: 'main-menu',
    component: MainMenu,
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisMenu,
    meta: { requiresAuth: true }
  },
  {
    path: '/inventory',
    name: 'inventory',
    component: () => import('../views/InventoryMenu.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/inventory/consulta-inventario',
    name: 'ConsultaInventario',
    component: () => import('../views/ConsultaInventario.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'consulta_inventario', permiso: 'ver' }
  },
  {
    path: '/inventory/consulta-lite',
    name: 'ConsultaInventarioLite',
    component: () => import('../views/ConsultaInventario_Lite.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'consulta', permiso: 'ver' }
  },
  {
    path: '/inventory/kardex',
    name: 'Kardex',
    component: () => import('../views/Kardex.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'kardex', permiso: 'ver' }
  },
  {
    path: '/inventory/gestion-productos-materiales',
    name: 'GestionProductosMateriales',
    component: () => import('../views/GestionProductosMateriales.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'gestion_productos', permiso: 'editar' }
  },
  {
    path: '/inventory/bodegas',
    name: 'BodegasForm',
    component: () => import('../views/BodegasForm.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'bodegas', permiso: 'ver' }
  },
  {
    path: '/inventory/trasladar-cantidades',
    name: 'TrasladarCantidades',
    component: () => import('../views/TrasladarCantidades.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'traslados', permiso: 'ver' }
  },
  {
    path: '/inventory/cargar-compras',
    name: 'CargarComprasProducto',
    component: () => import('../views/CargarComprasProducto.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'compras', permiso: 'ver' }
  },
  {
    path: '/inventory/ventas',
    name: 'CargarVentasManual',
    component: () => import('../views/CargarVentasManual.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'ventas', permiso: 'ver' }
  },
  {
    path: '/inventory/notas-credito',
    name: 'CargarNotasCredito',
    component: () => import('../views/CargarNotasCredito.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'notas_credito', permiso: 'ver' }
  },
  {
    path: '/inventory/ajuste-inventario',
    name: 'AjusteInventario',
    component: () => import('../views/AjusteInventario.vue'),
    meta: { requiresAuth: true, seccion: 'inventario', subseccion: 'ajustes', permiso: 'ver' }
  },
  {
    path: '/production',
    name: 'production',
    component: () => import('../views/ProductionMenu.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/production/admin',
    name: 'ProduccionAdmin',
    component: () => import('../views/ProduccionAdmin.vue'),
    meta: { requiresAuth: true, seccion: 'production', subseccion: 'admin', permiso: 'ver' }
  },
  {
    path: '/production/reportes',
    name: 'ReportesProduccion',
    component: () => import('../views/ReportesProduccion.vue'),
    meta: { requiresAuth: true, seccion: 'production', subseccion: 'reportes', permiso: 'ver' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsMenu.vue'),
    meta: { requiresAuth: true, seccion: 'parametrizacion', permiso: 'editar' }
  },
  { path: '/login', name: 'Login', component: Login },
  { path: '/upload', name: 'UploadMenu', component: UploadMenu, meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' } },
  { path: '/upload/sales', name: 'UploadSales', component: UploadSales, meta: { requiresAuth: true, seccion: 'cargue', subseccion: 'ventas_diarias', permiso: 'editar' } },
  { path: '/upload/arqueo', name: 'UploadArqueo', component: UploadArqueo, meta: { requiresAuth: true, seccion: 'cargue', subseccion: 'arqueo', permiso: 'editar' } },
  { path: '/upload/venta-mensual', name: 'UploadVentaMensual', component: UploadVentaMensual, meta: { requiresAuth: true, seccion: 'cargue', subseccion: 'venta_mensual_historica', permiso: 'editar' } },
  { path: '/upload/budget', name: 'UploadBudget', component: UploadBudget, meta: { requiresAuth: true, seccion: 'cargue', subseccion: 'presupuesto_venta', permiso: 'editar' } },
  { path: '/dashboard', name: 'Dashboard', component: DashboardMenu, meta: { requiresAuth: true, seccion: 'dashboard', permiso: 'ver' } },
  { path: '/dashboard/historical-sales', name: 'HistoricalSales', component: HistoricalSales, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_historicas', permiso: 'ver' } },
  { path: '/dashboard/monthly-performance', name: 'MonthlyPerformance', component: MonthlyPerformance, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'rendimiento_mensual', permiso: 'ver' } },
  { path: '/dashboard/daily-sales', name: 'DailySales', component: DailySales, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'venta_diaria_pdv', permiso: 'ver' } },
  { path: '/dashboard/sales-by-time-slot', name: 'SalesByTimeSlot', component: SalesByTimeSlot, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_franja_dia', permiso: 'ver' } },
  { path: '/dashboard/sales-by-payment-method', name: 'SalesByPaymentMethod', component: SalesByPaymentMethod, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_medio_pago', permiso: 'ver' } },
  { path: '/dashboard/sales-by-product', name: 'SalesByProduct', component: SalesByProduct, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_producto', permiso: 'ver' } },
  { path: '/dashboard/sales-by-seller', name: 'SalesBySeller', component: SalesBySeller, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_asesor', permiso: 'ver' } },
  { path: '/dashboard/accumulated-sales-by-pdv', name: 'AccumulatedSalesByPDV', component: AccumulatedSalesByPDV, meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'venta_acumulada_pdv', permiso: 'ver' } },
  { path: '/points-of-sale', name: 'PointsOfSale', component: PointsOfSale, meta: { requiresAuth: true, seccion: 'cargue', subseccion: 'puntos_de_venta', permiso: 'editar' } },
  { path: '/profiles-clientes', name: 'ProfilesClientes', component: ProfilesClientes, meta: { requiresAuth: true, seccion: 'parametrizacion', subseccion: 'perfiles', permiso: 'editar' } },
  { path: '/users-clientes', name: 'UsersClientes', component: UsersClientes, meta: { requiresAuth: true, seccion: 'parametrizacion', subseccion: 'usuarios', permiso: 'editar' } },
  {
    path: '/cutoff-config',
    name: 'CutoffConfig',
    component: CutoffConfig,
    meta: { requiresAuth: true, seccion: 'parametrizacion', subseccion: 'cutoff', permiso: 'editar' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresSuperAdmin: true },
    children: [
      { path: 'clientes', name: 'Clientes', component: Clientes, meta: { seccion: 'administracion', subseccion: 'crear_clientes', permiso: 'crear' } },
      { path: 'perfiles', name: 'Profiles', component: Profiles, meta: { seccion: 'administracion', subseccion: 'crear_perfiles', permiso: 'crear' } },
      { path: 'usuarios', name: 'Users', component: Users, meta: { seccion: 'administracion', subseccion: 'crear_usuarios', permiso: 'crear' } }
    ]
  }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const store = useStore();
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!store.getters.isAuthenticated) {
      next('/login');
      return;
    }
    if (to.matched.some(record => record.meta.requiresSuperAdmin)) {
      if (!store.getters.isSuperAdmin) {
        next('/');
        return;
      }
      next();
      return;
    }
    if (store.state.auth.idcliente && store.state.cliente.estado === false) {
      store.commit('logout');
      next('/login');
      return;
    }
    const permissionRecords = to.matched.filter(record => record.meta.seccion);
    if (permissionRecords.length > 0) {
      for (const record of permissionRecords) {
        const { seccion, subseccion, permiso } = record.meta;
        if (!store.getters.hasPermission(seccion, subseccion, permiso)) {
          console.log(`Permiso denegado para ${seccion}/${subseccion}/${permiso}`);
          next('/');
          return;
        }
      }
    }
    if (store.state.auth.idcliente && !store.state.cliente.nombre) {
      store.dispatch('fetchCliente').then(() => {
        next();
      }).catch(() => {
        next('/');
      });
    } else {
      next();
    }
  } else {
    if (to.path === '/login' && store.getters.isAuthenticated) {
      if (store.getters.isSuperAdmin) {
        next('/admin');
      } else {
        next('/');
      }
      return;
    }
    next();
  }
});

export default router;