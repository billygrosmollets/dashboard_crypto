<template>
  <div class="portfolio-view">
    <div class="view-header">
      <h1>Portfolio Dashboard</h1>
      <div class="view-actions">
        <button @click="handleManualRefresh" :disabled="loading">
          {{ loading ? 'Rafraîchissement...' : 'Actualiser' }}
        </button>
      </div>
    </div>

    <div class="auto-refresh-indicator">
      <span class="indicator-dot"></span>
      Auto-refresh actif (60s) - Prochain rafraîchissement dans {{ countdown }}s
    </div>

    <PortfolioTable />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { usePortfolioStore } from '../stores/portfolio'
import { usePolling } from '../composables/usePolling'
import PortfolioTable from '../components/PortfolioTable.vue'

const portfolioStore = usePortfolioStore()
const { loading } = storeToRefs(portfolioStore)

const countdown = ref(60)
let countdownTimer = null

// Auto-refresh every 60 seconds (matches original Tkinter app)
usePolling(async () => {
  await portfolioStore.fetchBalances()
  resetCountdown()
}, 60000)

// Manual refresh handler
async function handleManualRefresh() {
  await portfolioStore.refreshPortfolio()
  resetCountdown()
}

// Countdown timer for UI feedback
function resetCountdown() {
  countdown.value = 60
}

function startCountdownTimer() {
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    }
  }, 1000)
}

onMounted(() => {
  startCountdownTimer()
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.portfolio-view {
  max-width: 1500px;
  margin: 0 auto;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem 0;
}

.view-header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(135deg, var(--gray-800), var(--gold-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.view-actions {
  display: flex;
  gap: 1rem;
}

.view-actions button {
  padding: 0.9rem 1.8rem;
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  color: var(--bg-primary);
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  position: relative;
  overflow: hidden;
}

.view-actions button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.view-actions button:active::before {
  width: 300px;
  height: 300px;
}

.view-actions button:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--gold-primary), var(--gold-dark));
}

.view-actions button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

/* Glassmorphism Refresh Indicator */
.auto-refresh-indicator {
  background: var(--glass-bg);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid var(--glass-border);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.9rem;
  color: var(--gray-600);
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.indicator-dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, var(--success), #66bb6a);
  border-radius: 50%;
  box-shadow: 0 0 12px var(--success);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}
</style>
