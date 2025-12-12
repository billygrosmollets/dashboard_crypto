<template>
  <div class="twr-analytics-view">
    <div class="header">
      <h1>Performance Analytics</h1>
      <div class="header-actions">
        <button
          @click="createManualSnapshot"
          class="btn-snapshot"
          :disabled="loading"
        >
          {{ loading ? 'Création...' : 'Créer un snapshot maintenant' }}
        </button>
        <button
          @click="refreshData"
          class="btn-refresh"
          :disabled="loading"
        >
          {{ loading ? 'Chargement...' : 'Rafraîchir' }}
        </button>
      </div>
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

      <!-- Auto-refresh info -->
      <section class="section info-section">
        <div class="info-box">
          <h4>Information</h4>
          <p>
            Les snapshots sont automatiquement créés toutes les 2 heures (120 refreshes de 60 secondes).
            Vous pouvez aussi créer un snapshot manuellement à tout moment avec le bouton ci-dessus.
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
import { usePolling } from '@/composables/usePolling'
import TWRMetrics from '@/components/TWRMetrics.vue'
import CashFlowForm from '@/components/CashFlowForm.vue'

const performanceStore = usePerformanceStore()
const { loading, hasData } = storeToRefs(performanceStore)

// Refresh data every 2 minutes (performance data doesn't change as frequently as portfolio)
usePolling(() => {
  performanceStore.refreshAllData()
}, 120000) // 2 minutes

onMounted(() => {
  performanceStore.refreshAllData()
})

async function refreshData() {
  try {
    await performanceStore.refreshAllData()
  } catch (error) {
    console.error('Erreur lors du rafraîchissement:', error)
  }
}

async function createManualSnapshot() {
  try {
    await performanceStore.createSnapshot()

    // Refresh all data including TWR calculations
    await performanceStore.refreshAllData()
  } catch (error) {
    console.error('Erreur lors de la création du snapshot:', error)
    alert('Erreur lors de la création du snapshot: ' + error.message)
  }
}
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

.header-actions {
  display: flex;
  gap: 1rem;
}

button {
  padding: 0.9rem 1.8rem;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

button::before {
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

button:active::before {
  width: 300px;
  height: 300px;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-snapshot {
  background: linear-gradient(135deg, var(--info), #1976d2);
  color: white;
  box-shadow: 0 4px 12px rgba(66, 165, 245, 0.3);
}

.btn-snapshot:hover:not(:disabled) {
  background: linear-gradient(135deg, #1976d2, var(--info));
}

.btn-refresh {
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  color: var(--bg-primary);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  font-weight: 800;
}

.btn-refresh:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--gold-primary), var(--gold-dark));
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
