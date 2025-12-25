<template>
  <div class="portfolio-table">
    <div class="table-header">

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
        </div>

        <!-- Grid Rows -->
        <div class="grid-row" v-for="balance in sortedBalances" :key="balance.asset">
          <div class="grid-cell asset-name">
            <strong>{{ balance.asset }}</strong>
          </div>
          <div class="grid-cell">{{ formatBalance(balance.balance) }}</div>
          <div class="grid-cell usd-value">${{ balance.usd_value.toFixed(2) }}</div>
          <div class="grid-cell percentage">{{ balance.percentage.toFixed(2) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { usePortfolioStore } from '../stores/portfolio'

const portfolioStore = usePortfolioStore()
const { sortedBalances, formattedTotal, balancesCount, formattedLastUpdated, loading, error } = storeToRefs(portfolioStore)

function formatBalance(value) {
  if (value === 0) return '0'
  if (value < 0.000001) return value.toExponential(2)
  if (value < 0.01) return value.toFixed(8)
  if (value < 1) return value.toFixed(6)
  return value.toFixed(4)
}
</script>

<style scoped>
/* Terminal Portfolio Table */
.portfolio-table {
  background: var(--bg-primary);
  border: none;
  padding: 1.5rem;
  width: 100%;
  font-family: inherit;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(34, 197, 94, 0.3);
}

.card-title {
  color: #4ade80;
  font-size: 1.2rem;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.table-stats {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 500;
  color: #4ade80;
  letter-spacing: 1px;
}

.asset-count {
  font-size: 0.95rem;
  color: rgba(74, 222, 128, 0.6);
  font-weight: 500;
  text-transform: uppercase;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  color: #4ade80;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.error {
  color: #f87171;
  border: 1px solid rgba(255, 0, 0, 0.3);
  background: var(--bg-secondary);
  border-radius: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: rgba(74, 222, 128, 0.6);
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Terminal Table */
.table-wrapper {
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
}

.grid-table {
  display: flex;
  flex-direction: column;
  min-width: 100%;
  background: var(--bg-secondary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.5rem;
  overflow: hidden;
}

/* Grid Header */
.grid-header {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--bg-primary);
  border-bottom: 1px solid rgba(34, 197, 94, 0.3);
  align-items: center;
}

/* Grid Row */
.grid-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid rgba(34, 197, 94, 0.3);
  transition: background 0.2s ease;
  align-items: center;
}

.grid-row:hover {
  background: var(--gray-100);
  border-bottom-color: #22c55e;
}

.grid-row:last-child {
  border-bottom: none;
}

/* Grid Cells */
.grid-cell {
  display: flex;
  align-items: center;
  color: #4ade80;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-cell {
  color: #4ade80;
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 500;
  letter-spacing: 1px;
  white-space: nowrap;
}

.asset-name {
  font-weight: 500;
  color: #4ade80;
  font-size: 0.95rem;
  letter-spacing: 1px;
}

.usd-value {
  font-weight: 500;
  color: #4ade80;
}

.percentage {
  color: rgba(74, 222, 128, 0.6);
  font-weight: 500;
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
}

@media (max-width: 992px) {
  .grid-header,
  .grid-row {
    gap: 0.4rem;
    padding: 0.75rem 0.75rem;
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
    min-width: 500px;
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
}

@media (max-width: 576px) {
  .portfolio-table {
    padding: 0.75rem;
  }

  .card-title {
    font-size: 1.25rem;
  }

  .grid-table {
    min-width: 450px;
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
}
</style>


