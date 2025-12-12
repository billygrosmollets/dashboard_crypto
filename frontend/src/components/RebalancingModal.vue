<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Plan de Rebalancing</h3>
        <button class="btn-close" @click="$emit('cancel')">×</button>
      </div>

      <div class="modal-body">
        <div class="plan-summary">
          <div class="summary-item">
            <span class="label">Portfolio Total:</span>
            <span class="value">${{ formatNumber(plan.total_value_usd) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Actions:</span>
            <span class="value">{{ plan.actions.length }}</span>
          </div>
        </div>

        <div v-if="plan.actions.length === 0" class="no-actions">
          Portfolio déjà aligné avec l'allocation cible
        </div>

        <div v-else class="actions-list">
          <div
            v-for="(action, index) in plan.actions"
            :key="index"
            class="action-item"
            :class="action.action.toLowerCase()"
          >
            <div class="action-icon" :class="action.action.toLowerCase()">
              {{ action.action === 'ACHETER' ? 'BUY' : 'SELL' }}
            </div>
            <div class="action-details">
              <div class="action-header">
                <span class="asset">{{ action.asset }}</span>
                <span class="action-type">{{ action.action }}</span>
              </div>
              <div class="action-amount">
                ${{ formatNumber(action.usd_amount) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('cancel')">
          Annuler
        </button>
        <button
          class="btn-confirm"
          @click="$emit('confirm')"
          :disabled="plan.actions.length === 0"
        >
          Exécuter
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useFormatting } from '@/composables/useFormatting'

defineProps({
  plan: {
    type: Object,
    required: true
  }
})

defineEmits(['confirm', 'cancel'])

const { formatNumber } = useFormatting()
</script>

<style scoped>
/* Glassmorphism Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(8px);
  }
}

.modal-content {
  background: var(--glass-bg);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  max-width: 650px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.6);
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
}

.modal-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold-primary), transparent);
  opacity: 0.3;
}

@keyframes slideUp {
  from {
    transform: translateY(100px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  border-bottom: 1px solid var(--glass-border);
}

.modal-header h3 {
  color: var(--gray-800);
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.5px;
}

.btn-close {
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--glass-border);
  color: var(--gray-500);
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.btn-close:hover {
  background: rgba(212, 175, 55, 0.2);
  color: var(--gold-primary);
  transform: rotate(90deg);
  border-color: var(--gold-primary);
}

.modal-body {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
}

/* Custom modal scrollbar */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: rgba(28, 28, 28, 0.3);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--gold-dark), var(--gold-primary));
  border-radius: 4px;
}

.plan-summary {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  background: rgba(212, 175, 55, 0.08);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.summary-item .label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
}

.summary-item .value {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.no-actions {
  text-align: center;
  padding: 3rem;
  color: var(--success);
  font-size: 1.25rem;
  font-weight: 700;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-item {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(28, 28, 28, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.action-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.05), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.action-item:hover::before {
  opacity: 1;
}

.action-item:hover {
  background: rgba(28, 28, 28, 0.6);
  border-left-width: 4px;
}

.action-item.acheter {
  border-left-color: var(--success);
}

.action-item.vendre {
  border-left-color: var(--error);
}

.action-icon {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-icon.acheter {
  background: rgba(76, 175, 80, 0.2);
  color: var(--success);
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.action-icon.vendre {
  background: rgba(239, 83, 80, 0.2);
  color: var(--error);
  border: 1px solid rgba(239, 83, 80, 0.3);
}

.action-details {
  flex: 1;
}

.action-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.asset {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--gray-800);
  letter-spacing: 0.5px;
}

.action-type {
  font-size: 0.7rem;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}

.action-amount {
  font-size: 0.95rem;
  color: var(--gray-600);
  font-weight: 600;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  padding: 2rem;
  border-top: 1px solid var(--glass-border);
  background: rgba(10, 10, 10, 0.3);
}

button {
  flex: 1;
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
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

.btn-cancel {
  background: rgba(117, 117, 117, 0.3);
  border: 1px solid var(--glass-border);
  color: var(--gray-600);
  backdrop-filter: blur(10px);
}

.btn-cancel:hover:not(:disabled) {
  background: rgba(117, 117, 117, 0.5);
  color: var(--gray-700);
}

.btn-confirm {
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  color: var(--bg-primary);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.3);
  font-weight: 800;
}

.btn-confirm:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--gold-primary), var(--gold-dark));
}
</style>
