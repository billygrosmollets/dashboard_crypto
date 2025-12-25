<template>
  <div class="terminal-dashboard">
    <!-- Header fixe -->
    <header class="dashboard-header">
      <div class="header-left">
        <span class="title">&gt; CryptoTracker_</span>
      </div>
      <div class="header-center">
        <button @click="openBalanceModal" class="balance-btn">
          {{ formattedTotal }}
        </button>
        <button @click="handleRefresh" class="refresh-btn" :disabled="refreshing">
          {{ refreshing ? 'Refreshing...' : '↻ Refresh' }}
        </button>
        <button @click="openCashFlowModal" class="cashflow-btn">
          Cashflow
        </button>
      </div>
      <div class="header-right">
        <UTCClock />
      </div>
    </header>

    <!-- Main content: Chart + Metrics -->
    <main class="main-content">
      <div v-if="loading" class="loading">
        LOADING DATA...
      </div>

      <div v-else-if="error" class="error">
        ERROR: {{ error }}
      </div>

      <template v-else>
        <!-- Top: TWR Chart (full width) -->
        <div class="chart-section">
          <TWRChart />
        </div>

        <!-- Bottom: Metrics Cards (horizontal grid) -->
        <div class="metrics-grid">
          <MetricCard
            v-for="period in periods"
            :key="period.key"
            :period="period"
            :data="combinedMetrics[period.key]"
          />
        </div>
      </template>
    </main>

    <!-- Modal Balance -->
    <dialog ref="balanceDialog" class="terminal-modal">
      <div class="modal-header">
        <h2>[ PORTFOLIO HOLDINGS ]</h2>
        <button @click="closeBalanceModal" class="close-btn">[X]</button>
      </div>
      <PortfolioTable />
    </dialog>

    <!-- Modal CashFlow -->
    <dialog ref="cashFlowDialog" class="terminal-modal cashflow-modal">
      <div class="modal-header">
        <h2>[ CASH FLOW MANAGEMENT ]</h2>
        <button @click="closeCashFlowModal" class="close-btn">[X]</button>
      </div>
      <CashFlowForm @cash-flow-added="onCashFlowAdded" />
    </dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import axios from 'axios'
import { usePortfolioStore } from '@/stores/portfolio'
import { usePerformanceStore } from '@/stores/performance'
import UTCClock from '@/components/UTCClock.vue'
import MetricCard from '@/components/MetricCard.vue'
import PortfolioTable from '@/components/PortfolioTable.vue'
import CashFlowForm from '@/components/CashFlowForm.vue'
import TWRChart from '@/components/TWRChart.vue'

const portfolioStore = usePortfolioStore()
const performanceStore = usePerformanceStore()

const { formattedTotal } = storeToRefs(portfolioStore)
const { combinedMetrics, loading, error } = storeToRefs(performanceStore)

const balanceDialog = ref(null)
const cashFlowDialog = ref(null)
const isConnected = ref(false)
const refreshing = ref(false)

const periods = [
  { key: '7d', label: '7D' },
  { key: '14d', label: '14D' },
  { key: '30d', label: '30D' },
  { key: '60d', label: '60D' },
  { key: '180d', label: '180D' },
  { key: '365d', label: '365D' }
]

function openBalanceModal() {
  balanceDialog.value?.showModal()
}

function closeBalanceModal() {
  balanceDialog.value?.close()
}

function openCashFlowModal() {
  cashFlowDialog.value?.showModal()
}

function closeCashFlowModal() {
  cashFlowDialog.value?.close()
}

async function handleRefresh() {
  refreshing.value = true
  try {
    // Refresh both portfolio and performance data
    await Promise.all([
      portfolioStore.refreshPortfolio(),
      performanceStore.refreshAllData()
    ])
  } catch (error) {
    console.error('Error refreshing data:', error)
  } finally {
    refreshing.value = false
  }
}

function onCashFlowAdded() {
  // Refresh data after cash flow is added
  performanceStore.refreshAllData()
  // Optionally close modal
  // closeCashFlowModal()
}

onMounted(async () => {
  // Click outside to close
  balanceDialog.value?.addEventListener('click', (e) => {
    if (e.target === balanceDialog.value) closeBalanceModal()
  })

  cashFlowDialog.value?.addEventListener('click', (e) => {
    if (e.target === cashFlowDialog.value) closeCashFlowModal()
  })

  // Check connection status
  try {
    const response = await axios.get('/health')
    isConnected.value = response.data.trader_initialized === true
  } catch (error) {
    console.error('Connection test failed:', error)
    isConnected.value = false
  }

  // Initial data fetch
  portfolioStore.refreshPortfolio()
  performanceStore.refreshAllData()
})
</script>

<style scoped>
.terminal-dashboard {
  background: var(--bg-primary);
  min-height: 100vh;
}

.dashboard-header {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(0, 255, 65, 0.2);
  z-index: 1000;
}

.header-left .title {
  color: #4ade80;
  font-weight: normal;
}

.header-center {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.header-right {
  display: flex;
  justify-content: flex-end;
}

.balance-btn,
.cashflow-btn,
.refresh-btn {
  background: var(--bg-primary);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 0.5rem 1rem;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.balance-btn:hover,
.cashflow-btn:hover,
.refresh-btn:hover:not(:disabled) {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.main-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-section {
  height: 85vh;
  width: 100%;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1rem;
  width: 100%;
  min-height: 200px;
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.loading {
  color: var(--terminal-green);
}

.error {
  color: var(--error);
  border: 1px solid rgba(255, 0, 0, 0.3);
  background: var(--bg-secondary);
  border-radius: 0.75rem;
}

/* Responsive */
@media (max-width: 1400px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: auto;
  }
}

@media (max-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .chart-section {
    min-height: 350px;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .header-left,
  .header-center,
  .header-right {
    width: 100%;
    justify-content: center;
  }

  .header-center {
    flex-wrap: wrap;
  }

  .balance-btn,
  .cashflow-btn,
  .refresh-btn {
    font-size: 0.875rem;
    padding: 0.4rem 2rem;
  }

  .main-content {
    padding: 1rem;
    height: auto;
  }

  .chart-section {
    flex: none;
    height: auto;
    min-height: 300px;
  }

  .metrics-grid {
    flex: none;
    height: auto;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(4, 1fr);
  }
}
</style>
