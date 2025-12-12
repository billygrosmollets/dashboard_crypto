<template>
  <div class="rebalancing-panel">
    <h3>Rebalancing du Portfolio</h3>

    <div class="panel-actions">
      <button
        @click="calculateRebalancing"
        class="btn-calculate"
        :disabled="loading"
      >
        {{ loading ? 'Calcul en cours...' : '🔄 Calculer le Plan de Rebalancing' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="hasActions" class="rebalancing-plan">
      <div class="plan-header">
        <h4>Plan de Rebalancing</h4>
        <div class="plan-summary">
          <div class="summary-item">
            <span class="label">Portfolio Total:</span>
            <span class="value">${{ formatNumber(rebalancingPlan.total_value_usd) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Actions:</span>
            <span class="value">{{ rebalancingPlan.actions.length }}</span>
          </div>
        </div>
      </div>

      <div class="allocation-comparison">
        <div class="comparison-section">
          <h5>Allocation Actuelle</h5>
          <div class="allocation-bars">
            <div class="alloc-bar">
              <span>BTC</span>
              <div class="bar-container">
                <div
                  class="bar-fill btc"
                  :style="{ width: rebalancingPlan.current_allocation.btc + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.current_allocation.btc) }}</span>
            </div>
            <div class="alloc-bar">
              <span>ALT</span>
              <div class="bar-container">
                <div
                  class="bar-fill altcoins"
                  :style="{ width: rebalancingPlan.current_allocation.altcoin + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.current_allocation.altcoin) }}</span>
            </div>
            <div class="alloc-bar">
              <span>STABLE</span>
              <div class="bar-container">
                <div
                  class="bar-fill stablecoins"
                  :style="{ width: rebalancingPlan.current_allocation.stablecoin + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.current_allocation.stablecoin) }}</span>
            </div>
          </div>
        </div>

        <div class="arrow">→</div>

        <div class="comparison-section">
          <h5>Allocation Cible</h5>
          <div class="allocation-bars">
            <div class="alloc-bar">
              <span>BTC</span>
              <div class="bar-container">
                <div
                  class="bar-fill btc"
                  :style="{ width: rebalancingPlan.target_allocation.btc + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.target_allocation.btc) }}</span>
            </div>
            <div class="alloc-bar">
              <span>ALT</span>
              <div class="bar-container">
                <div
                  class="bar-fill altcoins"
                  :style="{ width: rebalancingPlan.target_allocation.altcoin + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.target_allocation.altcoin) }}</span>
            </div>
            <div class="alloc-bar">
              <span>STABLE</span>
              <div class="bar-container">
                <div
                  class="bar-fill stablecoins"
                  :style="{ width: rebalancingPlan.target_allocation.stablecoin + '%' }"
                ></div>
              </div>
              <span>{{ formatPercent(rebalancingPlan.target_allocation.stablecoin) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="actions-list">
        <h5>Actions à Exécuter</h5>
        <div class="actions-table">
          <div class="action-header">
            <span>Asset</span>
            <span>Action</span>
            <span>Montant USD</span>
            <span>Catégorie</span>
          </div>
          <div
            v-for="(action, index) in rebalancingPlan.actions"
            :key="index"
            class="action-row"
            :class="action.action.toLowerCase()"
          >
            <span class="asset">{{ action.asset }}</span>
            <span class="action-type">
              {{ action.action === 'ACHETER' ? '🟢 ACHETER' : '🔴 VENDRE' }}
            </span>
            <span class="amount">${{ formatNumber(action.usd_amount) }}</span>
            <span class="category">{{ getCategoryLabel(action.category) }}</span>
          </div>
        </div>
      </div>

      <div class="execution-section">
        <button
          @click="executeRebalancing"
          class="btn-execute"
          :disabled="executing"
        >
          {{ executing ? 'Exécution en cours...' : '⚡ Exécuter le Rebalancing' }}
        </button>
        <button
          @click="clearPlan"
          class="btn-cancel"
          :disabled="executing"
        >
          Annuler
        </button>
      </div>
    </div>

    <div v-if="executionResults" class="execution-results">
      <h4>Résultats de l'Exécution</h4>
      <div class="results-summary">
        <div class="summary-stat success">
          <span class="stat-label">Succès:</span>
          <span class="stat-value">{{ successCount }}</span>
        </div>
        <div class="summary-stat failed">
          <span class="stat-label">Échecs:</span>
          <span class="stat-value">{{ failedCount }}</span>
        </div>
        <div class="summary-stat fees">
          <span class="stat-label">Frais Totaux:</span>
          <span class="stat-value">${{ formatNumber(executionResults.total_fees_usd) }}</span>
        </div>
      </div>

      <div class="results-list">
        <div
          v-for="(result, index) in executionResults.results"
          :key="index"
          class="result-item"
          :class="{ success: result.success, failed: !result.success }"
        >
          <div class="result-icon">
            {{ result.success ? '✅' : '❌' }}
          </div>
          <div class="result-content">
            <div class="result-header">
              <span class="result-asset">{{ result.asset }}</span>
              <span class="result-action">{{ result.action }}</span>
            </div>
            <div class="result-message">{{ result.message }}</div>
            <div v-if="result.fees_usd > 0" class="result-fees">
              Frais: ${{ formatNumber(result.fees_usd) }}
            </div>
          </div>
        </div>
      </div>

      <button @click="closeResults" class="btn-close-results">
        Fermer
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRebalancingStore } from '@/stores/rebalancing'
import { usePortfolioStore } from '@/stores/portfolio'

const rebalancingStore = useRebalancingStore()
const portfolioStore = usePortfolioStore()

const { rebalancingPlan, loading, error, hasActions } = storeToRefs(rebalancingStore)

const executing = ref(false)
const executionResults = ref(null)

const successCount = computed(() => {
  if (!executionResults.value) return 0
  return executionResults.value.results.filter(r => r.success).length
})

const failedCount = computed(() => {
  if (!executionResults.value) return 0
  return executionResults.value.results.filter(r => !r.success).length
})

async function calculateRebalancing() {
  try {
    await rebalancingStore.calculatePlan()
  } catch (error) {
    console.error('Erreur lors du calcul du plan:', error)
  }
}

async function executeRebalancing() {
  if (!confirm('Êtes-vous sûr de vouloir exécuter ce plan de rebalancing ?')) {
    return
  }

  executing.value = true
  executionResults.value = null

  try {
    const results = await rebalancingStore.executePlan()
    executionResults.value = results

    // Refresh portfolio after execution
    await portfolioStore.refreshPortfolio()
  } catch (error) {
    console.error('Erreur lors de l\'exécution:', error)
    alert('Erreur lors de l\'exécution: ' + error.message)
  } finally {
    executing.value = false
  }
}

function clearPlan() {
  rebalancingStore.clearPlan()
}

function closeResults() {
  executionResults.value = null
}

function formatNumber(value) {
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function formatPercent(value) {
  return `${value.toFixed(2)}%`
}

function getCategoryLabel(category) {
  const labels = {
    'btc': '🟠 Bitcoin',
    'altcoins': '🔵 Altcoins',
    'stablecoins': '🟢 Stablecoins'
  }
  return labels[category] || category
}
</script>

<style scoped>
.rebalancing-panel {
  padding: 20px;
}

h3 {
  margin-bottom: 20px;
  color: #e0e0e0;
  font-size: 24px;
}

h4 {
  margin-bottom: 15px;
  color: #e0e0e0;
  font-size: 20px;
}

h5 {
  margin-bottom: 10px;
  color: #b0b0b0;
  font-size: 16px;
}

.panel-actions {
  margin-bottom: 20px;
}

button {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-calculate {
  background: #2196f3;
  color: white;
  width: 100%;
}

.btn-calculate:hover:not(:disabled) {
  background: #1976d2;
  transform: translateY(-2px);
}

.error-message {
  padding: 12px;
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
  border-radius: 4px;
  margin-bottom: 20px;
}

.rebalancing-plan {
  background: #2a2a2a;
  padding: 20px;
  border-radius: 8px;
}

.plan-header {
  margin-bottom: 20px;
}

.plan-summary {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.summary-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.summary-item .label {
  color: #888;
}

.summary-item .value {
  color: #e0e0e0;
  font-weight: 600;
}

.allocation-comparison {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #1a1a1a;
  border-radius: 8px;
}

.arrow {
  font-size: 32px;
  color: #4caf50;
}

.allocation-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alloc-bar {
  display: grid;
  grid-template-columns: 60px 1fr 60px;
  gap: 10px;
  align-items: center;
  font-size: 12px;
  color: #b0b0b0;
}

.bar-container {
  height: 20px;
  background: #0a0a0a;
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-fill.btc {
  background: linear-gradient(90deg, #f7931a, #ffb347);
}

.bar-fill.altcoins {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.bar-fill.stablecoins {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.actions-list {
  margin-bottom: 20px;
}

.actions-table {
  background: #1a1a1a;
  border-radius: 4px;
  overflow: hidden;
}

.action-header,
.action-row {
  display: grid;
  grid-template-columns: 100px 120px 1fr 150px;
  gap: 15px;
  padding: 12px 15px;
  align-items: center;
}

.action-header {
  background: #0a0a0a;
  color: #888;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.action-row {
  border-bottom: 1px solid #2a2a2a;
  font-size: 14px;
}

.action-row:last-child {
  border-bottom: none;
}

.action-row.acheter {
  border-left: 3px solid #4caf50;
}

.action-row.vendre {
  border-left: 3px solid #ff6b6b;
}

.asset {
  font-weight: 600;
  color: #e0e0e0;
}

.execution-section {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-execute {
  flex: 2;
  background: #4caf50;
  color: white;
}

.btn-execute:hover:not(:disabled) {
  background: #45a049;
}

.btn-cancel {
  flex: 1;
  background: #757575;
  color: white;
}

.btn-cancel:hover:not(:disabled) {
  background: #616161;
}

.execution-results {
  background: #2a2a2a;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.results-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.summary-stat {
  padding: 12px 20px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-stat.success {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid #4caf50;
}

.summary-stat.failed {
  background: rgba(255, 107, 107, 0.2);
  border: 1px solid #ff6b6b;
}

.summary-stat.fees {
  background: rgba(33, 150, 243, 0.2);
  border: 1px solid #2196f3;
}

.stat-label {
  font-size: 12px;
  color: #888;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #e0e0e0;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.result-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background: #1a1a1a;
  border-radius: 4px;
  border-left: 4px solid transparent;
}

.result-item.success {
  border-left-color: #4caf50;
}

.result-item.failed {
  border-left-color: #ff6b6b;
}

.result-icon {
  font-size: 24px;
}

.result-content {
  flex: 1;
}

.result-header {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
}

.result-asset {
  font-weight: 600;
  color: #e0e0e0;
}

.result-action {
  color: #888;
  font-size: 14px;
}

.result-message {
  color: #b0b0b0;
  font-size: 14px;
}

.result-fees {
  color: #888;
  font-size: 12px;
  margin-top: 5px;
}

.btn-close-results {
  background: #757575;
  color: white;
  width: 100%;
}

.btn-close-results:hover {
  background: #616161;
}

@media (max-width: 768px) {
  .allocation-comparison {
    grid-template-columns: 1fr;
  }

  .arrow {
    transform: rotate(90deg);
  }

  .action-header,
  .action-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}
</style>
