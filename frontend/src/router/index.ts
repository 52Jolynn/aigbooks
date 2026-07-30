import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/search', name: 'search', component: () => import('@/views/SearchView.vue') },
  { path: '/books/:isbn', name: 'book-detail', component: () => import('@/views/BookDetailView.vue') },
  { path: '/report', name: 'report', component: () => import('@/views/ReportView.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
