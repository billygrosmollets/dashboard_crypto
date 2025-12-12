import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useAPI } from '@/composables/useAPI'

export const usePerformanceStore = defineStore('performance', () => {
  const api = useAPI()

  // State
  const snapshots = ref([])
  const cashFlows = ref([])
  const twrMetrics = ref({
    '7d': null,
    '14d': null,
    '30d': null,
    '60d': null,
    '90d': null,
    '180d': null,
    '360d': null,
    '720d': null,
    'total': null
  })
  const pnlMetrics = ref({
    '7d': null,
    '14d': null,
    '30d': null,
    '60d': null,
    '90d': null,
    '180d': null,
    '360d': null,
    '720d': null,
    'total': null
  })
  const trackingStats = ref({
    first_snapshot_date: null,
    last_snapshot_date: null,
    total_snapshots: 0,
    total_cashflows: 0,
    total_deposits_usd: 0,
    total_withdrawals_usd: 0,
    tracking_days: 0
  })
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const netCashFlow = computed(() => {
    return trackingStats.value.total_deposits_usd - trackingStats.value.total_withdrawals_usd
  })

  const hasData = computed(() => {
    return snapshots.value.length > 0
  })

  const formattedLastSnapshot = computed(() => {
    if (!trackingStats.value.last_snapshot_date) return 'Aucun snapshot'
    const date = new Date(trackingStats.value.last_snapshot_date)
    return date.toLocaleString('fr-FR')
  })

  const combinedMetrics = computed(() => {
    const periods = ['7d', '14d', '30d', '60d', '90d', '180d', '360d', '720d', 'total']
    const result = {}

    periods.forEach(key => {
      const twr = twrMetrics.value[key]
      const pnl = pnlMetrics.value[key]

      if (twr || pnl) {
        result[key] = {
          // TWR data
          twr: twr?.twr,
          twr_percent: twr?.twr_percent,
          twr_annualized: twr?.twr_annualized,
          twr_annualized_percent: twr?.twr_annualized_percent,

          // P&L data
          realized_pnl: pnl?.realized_pnl_usd || 0,
          unrealized_pnl: pnl?.unrealized_pnl_usd || 0,
          total_pnl: pnl?.total_pnl_usd || 0,
          total_fees: pnl?.total_fees_usd || 0,
          trade_count: pnl?.trade_count || 0
        }
      } else {
        result[key] = null
      }
    })

    return result
  })

  // Actions
  async function fetchSnapshots(startDate = null, endDate = null, setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const params = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const data = await api.get('/performance/snapshots', { params })
      snapshots.value = data.snapshots

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors de la récupération des snapshots:', err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function fetchCashFlows(startDate = null, endDate = null, setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const params = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const data = await api.get('/performance/cashflows', { params })
      cashFlows.value = data.cashflows

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors de la récupération des cash flows:', err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function addCashFlow(type, amountUsd, description = '') {
    try {
      loading.value = true
      error.value = null

      const data = await api.post('/performance/cashflows', {
        type,
        amount_usd: amountUsd,
        description
      })

      // Refresh cash flows and stats after adding
      await fetchCashFlows()
      await fetchStats()

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors de l\'ajout du cash flow:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTWR(days, setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const data = await api.get(`/performance/twr/${days}`)

      // Store the result in the appropriate metric
      const key = days === 0 ? 'total' : `${days}d`
      twrMetrics.value[key] = data

      return data
    } catch (err) {
      error.value = err.message
      console.error(`Erreur lors du calcul du TWR ${days}d:`, err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function fetchPnL(days, setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const data = await api.get(`/performance/pnl/${days}`)

      // Store the result in the appropriate metric
      const key = days === 0 ? 'total' : `${days}d`
      pnlMetrics.value[key] = data

      return data
    } catch (err) {
      error.value = err.message
      console.error(`Erreur lors du calcul du P&L ${days}d:`, err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function fetchAllTWR(setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const periods = [7, 14, 30, 60, 90, 180, 360, 720, 0] // 0 = total

      // Fetch all TWR metrics in parallel without individual loading states
      await Promise.all(
        periods.map(days => fetchTWR(days, false))
      )
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors du calcul de tous les TWR:', err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function fetchAllPnL(setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const periods = [7, 14, 30, 60, 90, 180, 360, 720, 0] // 0 = total

      // Fetch all P&L metrics in parallel without individual loading states
      await Promise.all(
        periods.map(days => fetchPnL(days, false))
      )
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors du calcul de tous les P&L:', err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function fetchStats(setLoading = true) {
    try {
      if (setLoading) loading.value = true
      error.value = null

      const data = await api.get('/performance/stats')
      trackingStats.value = data

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors de la récupération des stats:', err)
      throw err
    } finally {
      if (setLoading) loading.value = false
    }
  }

  async function refreshAllData() {
    try {
      loading.value = true
      error.value = null

      // Fetch all data in parallel without individual loading states
      await Promise.all([
        fetchSnapshots(null, null, false),
        fetchCashFlows(null, null, false),
        fetchStats(false),
        fetchAllTWR(false),
        fetchAllPnL(false)
      ])
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors du rafraîchissement des données:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    snapshots,
    cashFlows,
    twrMetrics,
    pnlMetrics,
    combinedMetrics,
    trackingStats,
    loading,
    error,

    // Computed
    netCashFlow,
    hasData,
    formattedLastSnapshot,

    // Actions
    fetchSnapshots,
    fetchCashFlows,
    addCashFlow,
    fetchTWR,
    fetchPnL,
    fetchAllTWR,
    fetchAllPnL,
    fetchStats,
    refreshAllData
  }
})
