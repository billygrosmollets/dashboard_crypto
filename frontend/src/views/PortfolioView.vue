<template>
  <div class="portfolio-view">
    <div class="view-header">
      <h1>Portfolio Dashboard</h1>
      <span class="last-updated">Dernière mise à jour: {{ portfolioStore.formattedLastUpdated }}</span>
    </div>

    <PortfolioTable />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioTable from '../components/PortfolioTable.vue'

const portfolioStore = usePortfolioStore()

onMounted(() => {
  portfolioStore.fetchBalances()
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

.last-updated {
  font-size: 0.9rem;
  color: var(--gray-500);
  font-weight: 500;
}
</style>
