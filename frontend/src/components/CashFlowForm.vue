<template>
  <div class="cashflow-form">
    <h3>Ajouter un Cash Flow</h3>

    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="type">Type</label>
        <select id="type" v-model="formData.type" required>
          <option value="DEPOSIT">Dépôt</option>
          <option value="WITHDRAW">Retrait</option>
        </select>
      </div>

      <div class="form-group">
        <label for="amount">Montant (USD)</label>
        <input
          id="amount"
          v-model.number="formData.amount"
          type="number"
          step="0.01"
          min="0.01"
          placeholder="1000.00"
          required
        />
      </div>

      <div class="form-group">
        <label for="description">Description (optionnel)</label>
        <input
          id="description"
          v-model="formData.description"
          type="text"
          placeholder="Ex: Dépôt mensuel, Retrait partiel..."
          maxlength="200"
        />
      </div>

      <div class="form-actions">
        <button
          type="submit"
          class="btn-submit"
          :disabled="submitting"
        >
          {{ submitting ? 'Ajout en cours...' : 'Ajouter' }}
        </button>
        <button
          type="button"
          class="btn-reset"
          @click="resetForm"
          :disabled="submitting"
        >
          Réinitialiser
        </button>
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </form>

    <div class="cashflow-history">
      <h4>Historique des Cash Flows</h4>

      <div v-if="cashFlows.length === 0" class="no-cashflows">
        Aucun cash flow enregistré
      </div>

      <div v-else class="cashflows-list">
        <div
          v-for="cashflow in sortedCashFlows"
          :key="cashflow.id"
          class="cashflow-item"
          :class="cashflow.type.toLowerCase()"
        >
          <div class="cashflow-date">
            {{ formatDate(cashflow.timestamp) }}
          </div>
          <div class="cashflow-type">
            {{ cashflow.type === 'DEPOSIT' ? '📈 Dépôt' : '📉 Retrait' }}
          </div>
          <div class="cashflow-amount">
            {{ cashflow.type === 'DEPOSIT' ? '+' : '-' }}${{ formatNumber(cashflow.amount_usd) }}
          </div>
          <div v-if="cashflow.description" class="cashflow-description">
            {{ cashflow.description }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { usePerformanceStore } from '@/stores/performance'

const performanceStore = usePerformanceStore()
const { cashFlows } = storeToRefs(performanceStore)

const formData = ref({
  type: 'DEPOSIT',
  amount: null,
  description: ''
})

const submitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const sortedCashFlows = computed(() => {
  return [...cashFlows.value].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp)
  })
})

async function handleSubmit() {
  if (!formData.value.amount || formData.value.amount <= 0) {
    errorMessage.value = 'Le montant doit être supérieur à 0'
    return
  }

  submitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await performanceStore.addCashFlow(
      formData.value.type,
      formData.value.amount,
      formData.value.description
    )

    successMessage.value = `Cash flow de $${formData.value.amount} ajouté avec succès`
    resetForm()

    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    errorMessage.value = error.message || 'Erreur lors de l\'ajout du cash flow'
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  formData.value = {
    type: 'DEPOSIT',
    amount: null,
    description: ''
  }
  errorMessage.value = ''
}

function formatNumber(value) {
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString('fr-FR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.cashflow-form {
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

/* Glassmorphism Form */
form {
  background: rgba(212, 175, 55, 0.05);
  backdrop-filter: blur(15px);
  border: 1px solid var(--glass-border);
  padding: 2rem;
  border-radius: 14px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.75rem;
  color: var(--gold-primary);
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

select,
input[type="number"],
input[type="text"] {
  width: 100%;
  padding: 12px 16px;
  background: rgba(10, 10, 10, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  color: var(--gray-700);
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

select:focus,
input:focus {
  outline: none;
  border-color: var(--gold-primary);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
  background: rgba(212, 175, 55, 0.05);
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

button {
  padding: 14px 28px;
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

.btn-submit {
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  color: var(--bg-primary);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  flex: 1;
  font-weight: 800;
}

.btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--gold-primary), var(--gold-dark));
}

.btn-reset {
  background: rgba(117, 117, 117, 0.3);
  border: 1px solid var(--glass-border);
  color: var(--gray-600);
  backdrop-filter: blur(10px);
}

.btn-reset:hover:not(:disabled) {
  background: rgba(117, 117, 117, 0.5);
  color: var(--gray-700);
}

.success-message,
.error-message {
  margin-top: 1.5rem;
  padding: 1rem 1.25rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  backdrop-filter: blur(10px);
}

.success-message {
  background: rgba(76, 175, 80, 0.15);
  color: var(--success);
  border: 1px solid var(--success);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

.error-message {
  background: rgba(239, 83, 80, 0.15);
  color: var(--error);
  border: 1px solid var(--error);
  box-shadow: 0 4px 12px rgba(239, 83, 80, 0.2);
}

/* Glassmorphism History */
.cashflow-history {
  background: rgba(28, 28, 28, 0.5);
  backdrop-filter: blur(15px);
  border: 1px solid var(--glass-border);
  padding: 2rem;
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.no-cashflows {
  text-align: center;
  color: var(--gray-500);
  padding: 2rem;
  font-weight: 600;
}

.cashflows-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 450px;
  overflow-y: auto;
}

/* Custom scrollbar for cashflows list */
.cashflows-list::-webkit-scrollbar {
  width: 8px;
}

.cashflows-list::-webkit-scrollbar-track {
  background: rgba(28, 28, 28, 0.3);
  border-radius: 4px;
}

.cashflows-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--gold-dark), var(--gold-primary));
  border-radius: 4px;
}

.cashflow-item {
  display: grid;
  grid-template-columns: 150px 120px 1fr auto;
  gap: 1rem;
  align-items: center;
  padding: 1.25rem;
  background: rgba(10, 10, 10, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.cashflow-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.05), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cashflow-item:hover::before {
  opacity: 1;
}

.cashflow-item:hover {
  background: rgba(28, 28, 28, 0.6);
  border-left-width: 4px;
}

.cashflow-item.deposit {
  border-left-color: var(--success);
}

.cashflow-item.withdraw {
  border-left-color: var(--error);
}

.cashflow-date {
  font-size: 0.75rem;
  color: var(--gray-500);
  font-weight: 600;
}

.cashflow-type {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--gray-700);
}

.cashflow-amount {
  font-size: 1.1rem;
  font-weight: 800;
}

.cashflow-item.deposit .cashflow-amount {
  color: var(--success);
}

.cashflow-item.withdraw .cashflow-amount {
  color: var(--error);
}

.cashflow-description {
  font-size: 0.8rem;
  color: var(--gray-500);
  font-style: italic;
  grid-column: 1 / -1;
  margin-top: -0.5rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .cashflow-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .cashflow-description {
    margin-top: 0.5rem;
  }
}
</style>
