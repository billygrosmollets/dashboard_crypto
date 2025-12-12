import { createRouter, createWebHistory } from 'vue-router'
import PortfolioView from '../views/PortfolioView.vue'
import TWRAnalyticsView from '../views/TWRAnalyticsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'portfolio',
      component: PortfolioView
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: TWRAnalyticsView
    }
    // More routes will be added in later phases (Rebalancing, Converter)
  ]
})

export default router
