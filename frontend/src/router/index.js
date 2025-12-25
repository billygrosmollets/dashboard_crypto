import { createRouter, createWebHistory } from 'vue-router'
import UnifiedDashboard from '../components/UnifiedDashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: UnifiedDashboard
    }
  ]
})

export default router
