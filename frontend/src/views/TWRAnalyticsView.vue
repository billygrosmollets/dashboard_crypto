<template>
  <div class="twr-analytics-view">
    <div class="header">
      <h1>Performance Analytics</h1>
      <span class="last-updated">Dernier snapshot: {{ performanceStore.formattedLastSnapshot }}</span>
    </div>

    <div v-if="loading && !hasData" class="loading-container">
      <div class="loading-spinner">Chargement des données...</div>
    </div>

    <div v-else class="content">
      <!-- TWR Metrics Section -->
      <section class="section">
        <TWRMetrics />
      </section>

      <!-- Cash Flow Form Section -->
      <section class="section">
        <CashFlowForm />
      </section>

      <!-- Info section -->
      <section class="section info-section">
        <div class="info-box">
          <h4>Information</h4>
          <p>
            Les snapshots sont automatiquement créés toutes les 10 minutes par le backend.
            Rafraîchissez la page (F5) pour voir les dernières données.
          </p>
          <p>
            Les cash flows (dépôts/retraits) permettent de calculer précisément votre performance
            en excluant l'impact des ajouts et retraits de capital.
          </p>
          <p>
            Le TWR (Time-Weighted Return) mesure la performance pure de votre stratégie de trading,
            indépendamment du timing de vos dépôts et retraits.
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { usePerformanceStore } from '@/stores/performance'
import TWRMetrics from '@/components/TWRMetrics.vue'
import CashFlowForm from '@/components/CashFlowForm.vue'

const performanceStore = usePerformanceStore()
const { loading, hasData } = storeToRefs(performanceStore)

onMounted(() => {
  performanceStore.refreshAllData()
})
</script>

<style scoped>
.twr-analytics-view {
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem 0;
}

h1 {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(135deg, var(--gray-800), var(--gold-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.last-updated {
  font-size: 0.9rem;
  color: var(--gray-500);
  font-weight: 500;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-spinner {
  font-size: 1.25rem;
  color: var(--gray-600);
  font-weight: 600;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.05);
  }
}

.content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Glassmorphism Sections */
.section {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 8px 32px var(--glass-shadow);
  position: relative;
  overflow: hidden;
}

.section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold-primary), transparent);
  opacity: 0.2;
}

.info-section {
  background: rgba(212, 175, 55, 0.05);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(212, 175, 55, 0.2);
  padding: 2rem;
}

.info-box {
  color: var(--gray-600);
}

.info-box h4 {
  color: var(--gold-primary);
  margin-bottom: 1.25rem;
  font-size: 1.25rem;
  font-weight: 700;
}

.info-box p {
  margin-bottom: 0.75rem;
  line-height: 1.7;
  font-size: 0.95rem;
}

.info-box p:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  button {
    width: 100%;
  }
}
</style>
