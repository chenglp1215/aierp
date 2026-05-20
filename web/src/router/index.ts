import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../components/LoginView.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/sales-order',
    name: 'SalesOrder',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/purchase-order',
    name: 'PurchaseOrder',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/supplier',
    name: 'Supplier',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/finance/receivable',
    name: 'FinanceReceivable',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/sales',
    name: 'Sales',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/inventory',
    name: 'Inventory',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/finance',
    name: 'Finance',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/crm',
    name: 'Crm',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/pending-outbound',
    name: 'PendingOutbound',
    component: () => import('../components/DashboardLayout.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const isTokenExpired = (): boolean => {
  const tokenExpiresAt = localStorage.getItem('token_expires_at')
  if (!tokenExpiresAt) {
    const token = localStorage.getItem('token')
    return !token
  }
  return Date.now() > parseInt(tokenExpiresAt, 10)
}

const clearAuthData = () => {
  const keysToRemove = ['token', 'user', 'token_expires_at', 'remembered_username', 'remembered_password']
  keysToRemove.forEach(key => localStorage.removeItem(key))
}

router.beforeEach((to, _from, next) => {
  if (to.path === '/login') {
    const token = localStorage.getItem('token')
    if (token && !isTokenExpired()) {
      next('/dashboard')
      return
    }
    next()
    return
  }

  if (to.meta.requiresAuth) {
    if (isTokenExpired()) {
      clearAuthData()
      next('/login')
      return
    }
  }

  next()
})

export default router
