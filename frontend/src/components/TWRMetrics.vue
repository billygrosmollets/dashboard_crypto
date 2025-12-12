<template>
  <div class="twr-metrics">
    <h3>Performance Analytics</h3>

    <div v-if="loading" class="loading">
      Chargement des données...
    </div>

    <div v-else-if="error" class="error">
      Erreur: {{ error }}
    </div>

    <div v-else-if="!hasData" class="no-data">
      Aucune donnée disponible. Attendez le prochain snapshot automatique ou créez-en un manuellement.
    </div>

    <div v-else class="metrics-grid">
      <div
        v-for="period in periods"
        :key="period.key"
        class="metric-card"
        :class="getCardClass(combinedMetrics[period.key])"
      >
        <div class="metric-label">{{ period.label }}</div>

        <!-- TWR Value -->
        <div class="metric-row">
          <span class="metric-type">TWR:</span>
          <div class="metric-value">
            {{ formatTWR(combinedMetrics[period.key]) }}
          </div>
        </div>

        <!-- P&L Value -->
        <div class="metric-row pnl-row">
          <span class="metric-type">P&L:</span>
          <div class="metric-value pnl-value">
            {{ formatPnL(combinedMetrics[period.key]) }}
          </div>
        </div>

        <div v-if="combinedMetrics[period.key]" class="metric-details">
          <span class="detail-item">
            Réalisé: ${{ formatNumber(combinedMetrics[period.key].realized_pnl) }}
          </span>
          <span class="detail-item">
            Non-réalisé: ${{ formatNumber(combinedMetrics[period.key].unrealized_pnl) }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="hasData" class="stats-summary">
      <h4>Statistiques de tracking</h4>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">Période trackée:</span>
          <span class="stat-value">{{ trackingStats.tracking_days }} jours</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Snapshots totaux:</span>
          <span class="stat-value">{{ trackingStats.total_snapshots }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Dépôts totaux:</span>
          <span class="stat-value">${{ formatNumber(trackingStats.total_deposits_usd) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Retraits totaux:</span>
          <span class="stat-value">${{ formatNumber(trackingStats.total_withdrawals_usd) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Cash flow net:</span>
          <span class="stat-value" :class="netCashFlow >= 0 ? 'positive' : 'negative'">
            ${{ formatNumber(netCashFlow) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { usePerformanceStore } from '@/stores/performance'

const performanceStore = usePerformanceStore()
const { twrMetrics, pnlMetrics, combinedMetrics, trackingStats, loading, error, hasData, netCashFlow } = storeToRefs(performanceStore)

const periods = [
  { key: '7d', label: '7 jours' },
  { key: '14d', label: '14 jours' },
  { key: '30d', label: '30 jours' },
  { key: '60d', label: '60 jours' },
  { key: '90d', label: '90 jours' },
  { key: '180d', label: '180 jours' },
  { key: '360d', label: '1 an' },
  { key: '720d', label: '2 ans' },
  { key: 'total', label: 'Total' }
]

function formatTWR(metric) {
  if (!metric || metric.twr_percent === null || metric.twr_percent === undefined) {
    return 'N/A'
  }
  const value = metric.twr_percent
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function formatPnL(metric) {
  if (!metric || metric.total_pnl === null || metric.total_pnl === undefined) {
    return 'N/A'
  }
  const value = metric.total_pnl
  const sign = value >= 0 ? '+' : ''
  return `${sign}$${formatNumber(Math.abs(value))}`
}

function formatNumber(value) {
  if (value === null || value === undefined) return '0'
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function getCardClass(metric) {
  if (!metric || metric.twr_percent === null || metric.twr_percent === undefined) {
    return 'neutral'
  }
  return metric.twr_percent >= 0 ? 'positive' : 'negative'
}
</script>

<style scoped>
.twr-metrics {
  padding: 2rem;
}

h3 {
  margin-bottom: 2rem;
  color: var(--gray-800);
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

h4 {
  margin-bottom: 1.5rem;
  color: var(--gray-800);
  font-size: 1.25rem;
  font-weight: 700;
}

.loading, .error, .no-data {
  padding: 2rem;
  text-align: center;
  border-radius: 12px;
  background: rgba(28, 28, 28, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  color: var(--gray-600);
  font-weight: 600;
}

.error {
  color: var(--error);
  border-color: rgba(239, 83, 80, 0.3);
  background: rgba(239, 83, 80, 0.1);
}

.no-data {
  color: var(--warning);
  border-color: rgba(255, 152, 0, 0.3);
  background: rgba(255, 152, 0, 0.1);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

/* Glassmorphism Metric Cards */
.metric-card {
  padding: 1.75rem;
  border-radius: 14px;
  background: rgba(28, 28, 28, 0.5);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 2px solid transparent;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent, rgba(212, 175, 55, 0.05));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.metric-card:hover::before {
  opacity: 1;
}

.metric-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.metric-card.positive {
  border-color: var(--success);
  background: rgba(76, 175, 80, 0.05);
}

.metric-card.negative {
  border-color: var(--error);
  background: rgba(239, 83, 80, 0.05);
}

.metric-card.neutral {
  border-color: var(--gray-400);
  background: rgba(117, 117, 117, 0.05);
}

.metric-label {
  font-size: 0.8rem;
  color: var(--gold-primary);
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}

.metric-value {
  font-size: 2.25rem;
  font-weight: 800;
  margin-bottom: 1rem;
  letter-spacing: -0.5px;
  position: relative;
  z-index: 1;
}

.metric-card.positive .metric-value {
  color: var(--success);
  text-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
}

.metric-card.negative .metric-value {
  color: var(--error);
  text-shadow: 0 0 20px rgba(239, 83, 80, 0.3);
}

.metric-card.neutral .metric-value {
  color: var(--gray-600);
}

.metric-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--gray-500);
  position: relative;
  z-index: 1;
}

.detail-item {
  display: block;
  font-weight: 600;
}

/* Glassmorphism Stats Summary */
.stats-summary {
  background: rgba(212, 175, 55, 0.08);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(212, 175, 55, 0.2);
  padding: 2rem;
  border-radius: 14px;
  margin-top: 2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: rgba(28, 28, 28, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(28, 28, 28, 0.6);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-value.positive {
  background: linear-gradient(135deg, #66bb6a, var(--success));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-value.negative {
  background: linear-gradient(135deg, #ef5350, #e53935);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
