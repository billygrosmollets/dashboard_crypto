import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useAPI } from '@/composables/useAPI'

export const useRebalancingStore = defineStore('rebalancing', () => {
  const api = useAPI()

  // State
  const rebalancingPlan = ref({
    actions: [],
    current_allocation: {},
    target_allocation: {},
    total_value_usd: 0
  })

  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasActions = computed(() => {
    return rebalancingPlan.value.actions && rebalancingPlan.value.actions.length > 0
  })

  // Actions
  async function calculatePlan() {
    try {
      loading.value = true
      error.value = null

      const data = await api.post('/rebalancing/plan')
      rebalancingPlan.value = data

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors du calcul du plan:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function executePlan() {
    try {
      loading.value = true
      error.value = null

      const data = await api.post('/rebalancing/execute', {
        actions: rebalancingPlan.value.actions
      })

      // Clear plan after execution
      rebalancingPlan.value = {
        actions: [],
        current_allocation: {},
        target_allocation: {},
        total_value_usd: 0
      }

      return data
    } catch (err) {
      error.value = err.message
      console.error('Erreur lors de l\'exécution du rebalancing:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearPlan() {
    rebalancingPlan.value = {
      actions: [],
      current_allocation: {},
      target_allocation: {},
      total_value_usd: 0
    }
  }

  return {
    // State
    rebalancingPlan,
    loading,
    error,

    // Computed
    hasActions,

    // Actions
    calculatePlan,
    executePlan,
    clearPlan
  }
})
