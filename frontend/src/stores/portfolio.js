/**
 * Portfolio Store (Pinia)
 * Manages portfolio state and API interactions
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAPI } from '../composables/useAPI'

export const usePortfolioStore = defineStore('portfolio', () => {
  const api = useAPI()

  // State
  const balances = ref([])
  const totalValueUsd = ref(0)
  const lastUpdated = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const targetAllocations = ref({})

  // Computed
  const sortedBalances = computed(() => {
    // Filter assets >= 1% of portfolio, then sort by USD value
    return [...balances.value]
      .filter(b => b.percentage >= 1.0)
      .sort((a, b) => b.usd_value - a.usd_value)
  })

  const balancesCount = computed(() => sortedBalances.value.length)

  const formattedTotal = computed(() => {
    return `$${totalValueUsd.value.toFixed(2)}`
  })

  const formattedLastUpdated = computed(() => {
    if (!lastUpdated.value) return 'Jamais'
    const date = new Date(lastUpdated.value)
    return date.toLocaleString('fr-FR')
  })

  // Actions
  async function fetchBalances() {
    loading.value = true
    error.value = null

    try {
      const data = await api.get('/portfolio/balances')

      balances.value = data.balances || []
      totalValueUsd.value = data.total_value_usd || 0
      lastUpdated.value = data.last_updated

    } catch (err) {
      error.value = err.message || 'Erreur lors du chargement du portfolio'
      console.error('Error fetching balances:', err)
    } finally {
      loading.value = false
    }
  }

  async function refreshPortfolio() {
    loading.value = true
    error.value = null

    try {
      const data = await api.post('/portfolio/refresh')

      // Fetch updated balances after refresh
      await fetchBalances()

    } catch (err) {
      error.value = err.message || 'Erreur lors du rafraîchissement'
      console.error('Error refreshing portfolio:', err)
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    balances,
    totalValueUsd,
    lastUpdated,
    loading,
    error,
    targetAllocations,

    // Computed
    sortedBalances,
    balancesCount,
    formattedTotal,
    formattedLastUpdated,

    // Actions
    fetchBalances,
    refreshPortfolio
  }
})
