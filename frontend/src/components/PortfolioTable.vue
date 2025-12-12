<template>
  <div class="portfolio-table">
    <div class="table-header">
      <h2 class="card-title">Portfolio Holdings</h2>
      <div class="table-stats">
        <span class="total-value">{{ formattedTotal }}</span>
        <span class="asset-count">{{ balancesCount }} actifs</span>
      </div>
    </div>

    <div v-if="loading" class="loading">
      Chargement du portfolio...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="sortedBalances.length === 0" class="empty-state">
      Aucun actif trouvé
    </div>

    <div v-else class="table-wrapper">
      <!-- Grid Header -->
      <div class="grid-table">
        <div class="grid-header">
          <div class="grid-cell header-cell">Actif</div>
          <div class="grid-cell header-cell">Balance</div>
          <div class="grid-cell header-cell">Valeur USD</div>
          <div class="grid-cell header-cell">% Actuel</div>
          <div class="grid-cell header-cell">% Cible</div>
        </div>

        <!-- Grid Rows -->
        <div class="grid-row" v-for="balance in sortedBalances" :key="balance.asset">
          <div class="grid-cell asset-name">
            <strong>{{ balance.asset }}</strong>
          </div>
          <div class="grid-cell">{{ formatBalance(balance.balance) }}</div>
          <div class="grid-cell usd-value">${{ balance.usd_value.toFixed(2) }}</div>
          <div class="grid-cell percentage">{{ balance.percentage.toFixed(2) }}%</div>
          <div class="grid-cell target-cell">
            <input
              type="text"
              v-model.number="editableTargets[balance.asset]"
              class="target-input"
              placeholder="0.0"
            />
          </div>
        </div>
      </div>

      <div class="table-actions">
        <div class="total-indicator" :class="{ valid: isTotalValid, invalid: !isTotalValid }">
          <span class="label">Total:</span>
          <span class="value">{{ totalTarget.toFixed(2) }}%</span>
          <span v-if="!isTotalValid" class="warning">Doit être 100%</span>
          <span v-else class="check">OK</span>
        </div>

        <div class="action-buttons">
          <button @click="saveAndCalculate" class="btn-primary" :disabled="!isTotalValid || loading">
            Sauvegarder & Calculer Plan
          </button>
        </div>
      </div>
    </div>

    <!-- Rebalancing Plan Modal -->
    <RebalancingModal
      v-if="showModal"
      :plan="rebalancingPlan"
      @confirm="executeRebalancing"
      @cancel="closeModal"
    />

    <!-- Logs Panel -->
    <LogsPanel :logs="executionLogs" v-if="executionLogs.length > 0" @clear="clearLogs" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { usePortfolioStore } from '../stores/portfolio'
import { useAPI } from '../composables/useAPI'
import RebalancingModal from './RebalancingModal.vue'
import LogsPanel from './LogsPanel.vue'

const api = useAPI()
const portfolioStore = usePortfolioStore()
const { sortedBalances, formattedTotal, balancesCount, formattedLastUpdated, loading, error } = storeToRefs(portfolioStore)

const editableTargets = ref({})
const showModal = ref(false)
const rebalancingPlan = ref(null)
const executionLogs = ref([])

const totalTarget = computed(() => {
  return Object.values(editableTargets.value).reduce((sum, val) => sum + (parseFloat(val) || 0), 0)
})

const isTotalValid = computed(() => {
  return Math.abs(totalTarget.value - 100) < 0.01
})

onMounted(async () => {
  await loadTargets()
})

watch(sortedBalances, () => {
  // When balances change, make sure all assets have a target entry
  sortedBalances.value.forEach(balance => {
    if (editableTargets.value[balance.asset] === undefined) {
      editableTargets.value[balance.asset] = 0
    }
  })
})

async function loadTargets() {
  try {
    const data = await api.get('/rebalancing/allocation')
    const savedTargets = data.allocations || {}

    // Initialize targets for all significant assets
    editableTargets.value = {}
    sortedBalances.value.forEach(balance => {
      editableTargets.value[balance.asset] = savedTargets[balance.asset] || balance.percentage
    })
  } catch (err) {
    console.error('Error loading targets:', err)
    // Initialize with current percentages
    editableTargets.value = {}
    sortedBalances.value.forEach(balance => {
      editableTargets.value[balance.asset] = balance.percentage
    })
  }
}

async function saveAndCalculate() {
  if (!isTotalValid.value) {
    alert('Le total doit être égal à 100%')
    return
  }

  try {
    // Save allocations
    await api.post('/rebalancing/allocation', {
      allocations: editableTargets.value
    })

    // Calculate plan
    const planData = await api.post('/rebalancing/plan')
    rebalancingPlan.value = planData

    // Show modal
    showModal.value = true

  } catch (err) {
    alert('Erreur: ' + err.message)
    console.error('Error:', err)
  }
}

async function executeRebalancing() {
  showModal.value = false
  executionLogs.value = []

  addLog('Début de l\'exécution du rebalancing...', 'info')

  try {
    const result = await api.post('/rebalancing/execute', {
      actions: rebalancingPlan.value.actions
    })

    // Process results
    result.results.forEach(r => {
      if (r.success) {
        addLog(`${r.asset} ${r.action}: ${r.message}`, 'success')
        if (r.fees_usd > 0) {
          addLog(`   Frais: $${r.fees_usd.toFixed(2)}`, 'info')
        }
      } else {
        addLog(`${r.asset} ${r.action}: ${r.message}`, 'error')
      }
    })

    addLog(`Frais totaux: $${result.total_fees_usd.toFixed(2)}`, 'info')
    addLog('Rebalancing terminé', 'success')

    // Refresh portfolio
    await portfolioStore.refreshPortfolio()

  } catch (err) {
    addLog(`Erreur lors de l'exécution: ${err.message}`, 'error')
    console.error('Execution error:', err)
  }
}

function closeModal() {
  showModal.value = false
  rebalancingPlan.value = null
}

function addLog(message, type = 'info') {
  executionLogs.value.push({
    timestamp: new Date().toLocaleTimeString('fr-FR'),
    message,
    type
  })
}

function clearLogs() {
  executionLogs.value = []
}

function formatBalance(value) {
  if (value === 0) return '0'
  if (value < 0.000001) return value.toExponential(2)
  if (value < 0.01) return value.toFixed(8)
  if (value < 1) return value.toFixed(6)
  return value.toFixed(4)
}
</script>

<style scoped>
/* Glassmorphism Portfolio Table */
.portfolio-table {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px var(--glass-shadow);
  margin-bottom: 2rem;
  position: relative;
  overflow: visible;
  width: 100%;
}

.portfolio-table::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold-primary), transparent);
  opacity: 0.2;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--glass-border);
}

.card-title {
  color: var(--gray-700);
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.table-stats {
  display: flex;
  gap: 2.5rem;
  align-items: center;
}

.total-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--gold-primary);
  letter-spacing: -0.5px;
}

.asset-count {
  font-size: 0.95rem;
  color: var(--gray-500);
  font-weight: 500;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
  color: var(--gray-600);
}

.error {
  color: var(--error);
}

.empty-state {
  text-align: center;
  padding: 4rem;
  color: var(--gray-500);
  font-size: 1.1rem;
}

/* Table Wrapper - New Grid Approach */
.table-wrapper {
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  margin-bottom: 1.5rem;
}

.grid-table {
  display: flex;
  flex-direction: column;
  min-width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

/* Grid Header */
.grid-header {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid rgba(212, 175, 55, 0.1);
  align-items: center;
}

/* Grid Row */
.grid-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(212, 175, 55, 0.05);
  transition: background 0.2s ease;
  align-items: center;
}

.grid-row:hover {
  background: rgba(212, 175, 55, 0.08);
}

.grid-row:last-child {
  border-bottom: none;
}

/* Grid Cells */
.grid-cell {
  display: flex;
  align-items: center;
  color: var(--gray-600);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-cell {
  color: var(--gold-primary);
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.asset-name {
  font-weight: 700;
  color: var(--gray-700);
  font-size: 0.95rem;
  letter-spacing: 0.5px;
}

.usd-value {
  font-weight: 700;
  color: var(--gold-primary);
}

.percentage {
  color: var(--info);
  font-weight: 600;
}

/* Target Cell - Simple LineEdit Style */
.target-cell {
  width: 100%;
}

.target-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(139, 69, 19, 0.15);
  border: 2px solid rgba(139, 69, 19, 0.4);
  border-radius: 8px;
  color: #D4A574;
  font-size: 15px;
  font-weight: 700;
  text-align: center;
  transition: all 0.25s ease;
  outline: none;
}

.target-input::placeholder {
  color: rgba(139, 69, 19, 0.4);
  font-weight: 500;
}

.target-input:hover {
  background: rgba(139, 69, 19, 0.22);
  border-color: rgba(139, 69, 19, 0.6);
}

.target-input:focus {
  background: rgba(139, 69, 19, 0.25);
  border-color: #8B4513;
  box-shadow: 0 0 0 3px rgba(139, 69, 19, 0.15);
  color: #E6B87D;
}

/* Remove number input arrows (spinbox) */
.target-input::-webkit-outer-spin-button,
.target-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.target-input[type=number] {
  -moz-appearance: textfield;
}

/* Glassmorphism Action Bar */
.table-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(28, 28, 28, 0.5);
  backdrop-filter: blur(15px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  margin-top: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.total-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 700;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.total-indicator.valid {
  background: rgba(76, 175, 80, 0.15);
  color: var(--success);
  border: 2px solid var(--success);
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.2);
}

.total-indicator.invalid {
  background: rgba(239, 83, 80, 0.15);
  color: var(--error);
  border: 2px solid var(--error);
  box-shadow: 0 4px 16px rgba(239, 83, 80, 0.2);
}

.warning, .check {
  font-size: 0.9rem;
}

/* Enhanced Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
}

button {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
}

button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

button:active::before {
  width: 300px;
  height: 300px;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  color: var(--bg-primary);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  font-weight: 800;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--gold-primary), var(--gold-dark));
}

.table-footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--glass-border);
  color: var(--gray-500);
  font-size: 0.85rem;
  text-align: center;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .grid-header,
  .grid-row {
    gap: 0.6rem;
    padding: 0.875rem 1rem;
  }
}

@media (max-width: 1200px) {
  .portfolio-table {
    padding: 1.5rem;
  }

  .table-stats {
    gap: 1.5rem;
  }

  .total-value {
    font-size: 1.5rem;
  }

  .grid-header,
  .grid-row {
    gap: 0.5rem;
    padding: 0.75rem 0.875rem;
  }

  .grid-cell {
    font-size: 0.85rem;
  }

  .header-cell {
    font-size: 0.7rem;
  }

  .target-input {
    padding: 8px 12px;
    font-size: 13px;
  }
}

@media (max-width: 992px) {
  .grid-header,
  .grid-row {
    gap: 0.4rem;
    padding: 0.75rem 0.75rem;
  }

  .target-input {
    padding: 7px 10px;
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .portfolio-table {
    padding: 1rem;
    border-radius: 12px;
  }

  .table-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .card-title {
    font-size: 1.5rem;
  }

  .table-stats {
    gap: 1rem;
  }

  .total-value {
    font-size: 1.25rem;
  }

  .asset-count {
    font-size: 0.85rem;
  }

  .grid-table {
    min-width: 600px;
  }

  .grid-header,
  .grid-row {
    gap: 0.35rem;
    padding: 0.625rem 0.75rem;
  }

  .grid-cell {
    font-size: 0.8rem;
  }

  .header-cell {
    font-size: 0.65rem;
  }

  .asset-name {
    font-size: 0.8rem;
  }

  .target-input {
    padding: 6px 10px;
    font-size: 11px;
  }

  .table-actions {
    flex-direction: column;
    align-items: stretch;
    padding: 1rem;
  }

  .total-indicator {
    justify-content: center;
    padding: 10px 16px;
    font-size: 0.9rem;
  }

  button {
    width: 100%;
    padding: 12px 20px;
    font-size: 0.85rem;
  }

  .table-footer {
    font-size: 0.75rem;
  }
}

@media (max-width: 576px) {
  .portfolio-table {
    padding: 0.75rem;
  }

  .card-title {
    font-size: 1.25rem;
  }

  .grid-table {
    min-width: 520px;
  }

  .grid-header,
  .grid-row {
    gap: 0.3rem;
    padding: 0.5rem 0.5rem;
  }

  .grid-cell {
    font-size: 0.75rem;
  }

  .header-cell {
    font-size: 0.6rem;
    letter-spacing: 0.3px;
  }

  .target-input {
    padding: 5px 8px;
    font-size: 10px;
  }

  .total-indicator {
    font-size: 0.85rem;
    padding: 8px 12px;
  }

  .warning, .check {
    font-size: 0.8rem;
  }
}
</style>
