
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import Profile from '../views/Profile.vue'
import PasswordReset from '../views/PasswordReset.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: PasswordReset,
    meta: { requiresAuth: false }
  },
  {
    path: '/reset-password-confirm',
    name: 'ResetPasswordConfirm',
    component: () => import('../views/PasswordReset.vue'),
    meta: { requiresAuth: false }
  },

]


const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router