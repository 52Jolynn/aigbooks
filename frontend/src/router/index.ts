import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/search', name: 'search', component: () => import('@/views/SearchView.vue') },
  {
    path: '/identifiers/:type/:identifier',
    name: 'identifier-detail',
    component: () => import('@/views/IdentifierDetailView.vue'),
  },
  { path: '/report', name: 'report', component: () => import('@/views/ReportView.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
