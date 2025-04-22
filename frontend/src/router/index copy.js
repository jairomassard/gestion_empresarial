import { createRouter, createWebHashHistory } from 'vue-router';
import { useStore } from 'vuex';
import Login from '../views/Login.vue';
import HomeView from '../views/HomeView.vue';
import Admin from '../views/Admin.vue';
import Profiles from '../views/Profiles.vue';
import Users from '../views/Users.vue';
import UploadMenu from '../views/UploadMenu.vue'; // Nuevo componente para el menú de carga
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
import PointsOfSale from '../views/PointsOfSale.vue'; // Nuevo componente
import UsersAndProfiles from '../views/UsersAndProfiles.vue'; // Nuevo componente


const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
  // nuevas paginas
  { path: '/login', name: 'Login', component: Login },
  
  // Menú de carga de información
  { path: '/upload', name: 'UploadMenu', component: UploadMenu },
  { path: '/upload/sales', name: 'UploadSales', component: UploadSales },
  { path: '/upload/arqueo', name: 'UploadArqueo', component: UploadArqueo },
  { path: '/upload/venta-mensual', name: 'UploadVentaMensual', component: UploadVentaMensual },
  { path: '/upload/budget', name: 'UploadBudget', component: UploadBudget },
  // Menú de dashboards
  { path: '/dashboard', name: 'Dashboard', component: DashboardMenu },
  { path: '/dashboard/historical-sales', name: 'HistoricalSales', component: HistoricalSales },
  { path: '/dashboard/monthly-performance', name: 'MonthlyPerformance', component: MonthlyPerformance },
  { path: '/dashboard/daily-sales', name: 'DailySales', component: DailySales },
  { path: '/dashboard/sales-by-time-slot', name: 'SalesByTimeSlot', component: SalesByTimeSlot },
  { path: '/dashboard/sales-by-payment-method', name: 'SalesByPaymentMethod', component: SalesByPaymentMethod },
  { path: '/dashboard/sales-by-product', name: 'SalesByProduct', component: SalesByProduct },
  { path: '/dashboard/sales-by-seller', name: 'SalesBySeller', component: SalesBySeller },
  { path: '/dashboard/accumulated-sales-by-pdv', name: 'AccumulatedSalesByPDV', component: AccumulatedSalesByPDV },
  // Parametrización
  { path: '/points-of-sale', name: 'PointsOfSale', component: PointsOfSale },
  { path: '/users-and-profiles', name: 'UsersAndProfiles', component: UsersAndProfiles },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

export default router;
