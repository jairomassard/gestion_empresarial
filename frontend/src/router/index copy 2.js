import { createRouter, createWebHashHistory } from 'vue-router';
import { useStore } from 'vuex';
import Login from '../views/Login.vue';
import HomeView from '../views/HomeView.vue';
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
import UsersAndProfiles from '../views/UsersAndProfiles.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true } // Requiere autenticación
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue'),
    meta: { requiresAuth: true } // Requiere autenticación
  },
  // Página de login
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  // Menú de carga de información
  {
    path: '/upload',
    name: 'UploadMenu',
    component: UploadMenu,
    meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' }
  },
  {
    path: '/upload/sales',
    name: 'UploadSales',
    component: UploadSales,
    meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' }
  },
  {
    path: '/upload/arqueo',
    name: 'UploadArqueo',
    component: UploadArqueo,
    meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' }
  },
  {
    path: '/upload/venta-mensual',
    name: 'UploadVentaMensual',
    component: UploadVentaMensual,
    meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' }
  },
  {
    path: '/upload/budget',
    name: 'UploadBudget',
    component: UploadBudget,
    meta: { requiresAuth: true, seccion: 'cargue', permiso: 'editar' }
  },
  // Menú de dashboards
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardMenu,
    meta: { requiresAuth: true, seccion: 'dashboard' }
  },
  {
    path: '/dashboard/historical-sales',
    name: 'HistoricalSales',
    component: HistoricalSales,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_historicas', permiso: 'ver' }
  },
  {
    path: '/dashboard/monthly-performance',
    name: 'MonthlyPerformance',
    component: MonthlyPerformance,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'rendimiento_mensual', permiso: 'ver' }
  },
  {
    path: '/dashboard/daily-sales',
    name: 'DailySales',
    component: DailySales,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'venta_diaria_pdv', permiso: 'ver' }
  },
  {
    path: '/dashboard/sales-by-time-slot',
    name: 'SalesByTimeSlot',
    component: SalesByTimeSlot,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_franja_dia', permiso: 'ver' }
  },
  {
    path: '/dashboard/sales-by-payment-method',
    name: 'SalesByPaymentMethod',
    component: SalesByPaymentMethod,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_medio_pago', permiso: 'ver' }
  },
  {
    path: '/dashboard/sales-by-product',
    name: 'SalesByProduct',
    component: SalesByProduct,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_producto', permiso: 'ver' }
  },
  {
    path: '/dashboard/sales-by-seller',
    name: 'SalesBySeller',
    component: SalesBySeller,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'ventas_asesor', permiso: 'ver' }
  },
  {
    path: '/dashboard/accumulated-sales-by-pdv',
    name: 'AccumulatedSalesByPDV',
    component: AccumulatedSalesByPDV,
    meta: { requiresAuth: true, seccion: 'dashboard', subseccion: 'venta_acumulada_pdv', permiso: 'ver' }
  },
  // Parametrización
  {
    path: '/points-of-sale',
    name: 'PointsOfSale',
    component: PointsOfSale,
    meta: { requiresAuth: true, seccion: 'parametrizacion', permiso: 'editar' }
  },
  {
    path: '/users-and-profiles',
    name: 'UsersAndProfiles',
    component: UsersAndProfiles,
    meta: { requiresAuth: true, seccion: 'parametrizacion', permiso: 'editar' }
  },
  // Rutas para el superadministrador (usamos children aquí)
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresSuperAdmin: true },
    children: [
      {
        path: 'clientes',
        name: 'Clientes',
        component: Clientes,
        meta: { seccion: 'administracion', subseccion: 'crear_clientes', permiso: 'crear' }
      },
      {
        path: 'perfiles',
        name: 'Profiles',
        component: Profiles,
        meta: { seccion: 'administracion', subseccion: 'crear_perfiles', permiso: 'crear' }
      },
      {
        path: 'usuarios',
        name: 'Users',
        component: Users,
        meta: { seccion: 'administracion', subseccion: 'crear_usuarios', permiso: 'crear' }
      }
    ]
  }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const store = useStore();

  // Si la ruta requiere autenticación
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!store.getters.isAuthenticated) {
      next('/login');
      return;
    }

    // Si la ruta requiere superadministrador
    if (to.matched.some(record => record.meta.requiresSuperAdmin)) {
      if (!store.getters.isSuperAdmin) {
        next('/dashboard');
        return;
      }
      // Si es superadministrador, permitir acceso sin verificar permisos adicionales
      next();
      return;
    }

    // Verificar permisos solo para no superadministradores
    const permissionRecords = to.matched.filter(record => record.meta.seccion);
    for (const record of permissionRecords) {
      const { seccion, subseccion, permiso } = record.meta;
      if (!store.getters.hasPermission(seccion, subseccion, permiso)) {
        next('/dashboard');
        return;
      }
    }

    // Si es un usuario de cliente y no ha cargado la información del cliente
    if (store.state.auth.idcliente && !store.state.cliente.nombre) {
      store.dispatch('fetchCliente').then(() => {
        next();
      });
    } else {
      next();
    }
  } else {
    // Si la ruta no requiere autenticación (como /login)
    if (to.path === '/login' && store.getters.isAuthenticated) {
      if (store.getters.isSuperAdmin) {
        next('/admin');
      } else {
        next('/dashboard');
      }
      return;
    }
    next();
  }
});

export default router;