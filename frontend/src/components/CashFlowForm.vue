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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { usePerformanceStore } from '@/stores/performance'
import { useFormatting } from '@/composables/useFormatting'

const performanceStore = usePerformanceStore()
const { cashFlows } = storeToRefs(performanceStore)

const { formatNumber, formatDate } = useFormatting()

const formData = ref({
  type: 'DEPOSIT',
  amount: null
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
      formData.value.amount
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
    amount: null
  }
  errorMessage.value = ''
}
</script>

<style scoped>
.cashflow-form {
  padding: 1.5rem;
  font-family: inherit;
}

h3 {
  margin-bottom: 1.5rem;
  color: #4ade80;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
}

h4 {
  margin-bottom: 1.5rem;
  color: #4ade80;
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Terminal Form */
form {
  background: var(--bg-secondary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.75rem;
  color: #4ade80;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

select,
input[type="number"],
input[type="text"] {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-primary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
  font-size: 0.95rem;
  font-weight: 500;
  font-family: inherit;
  transition: border-color 0.2s;
  border-radius: 0.5rem;
}

select:focus,
input:focus {
  outline: none;
  border-color: #4ade80;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

button {
  padding: 0.75rem 1.5rem;
  border: 1px solid;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 0.5rem;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-submit {
  background: var(--bg-primary);
  border-color: #22c55e;
  color: #22c55e;
  flex: 1;
}

.btn-submit:hover:not(:disabled) {
  background: #22c55e;
  color: var(--bg-primary);
}

.btn-reset {
  background: var(--bg-primary);
  border-color: rgba(74, 222, 128, 0.6);
  color: rgba(74, 222, 128, 0.6);
}

.btn-reset:hover:not(:disabled) {
  background: rgba(74, 222, 128, 0.6);
  color: var(--bg-primary);
}

.success-message,
.error-message {
  margin-top: 1.5rem;
  padding: 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 0.5rem;
}

.success-message {
  background: var(--bg-secondary);
  color: #22c55e;
  border: 1px solid #22c55e;
}

.error-message {
  background: var(--bg-secondary);
  color: #f87171;
  border: 1px solid rgba(255, 0, 0, 0.3);
}

/* Terminal History */
.cashflow-history {
  background: var(--bg-secondary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 1.5rem;
  border-radius: 0.5rem;
}

.no-cashflows {
  text-align: center;
  color: rgba(74, 222, 128, 0.6);
  padding: 2rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cashflows-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 450px;
  overflow-y: auto;
}

/* Terminal scrollbar for cashflows list */
.cashflows-list::-webkit-scrollbar {
  width: 8px;
}

.cashflows-list::-webkit-scrollbar-track {
  background: var(--bg-primary);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.cashflows-list::-webkit-scrollbar-thumb {
  background: rgba(74, 222, 128, 0.6);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.cashflow-item {
  display: grid;
  grid-template-columns: 150px 120px 1fr;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  background: var(--bg-primary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.cashflow-item:hover {
  background: var(--gray-100);
  border-color: #4ade80;
}

.cashflow-item.deposit {
  border-left-color: #22c55e;
}

.cashflow-item.withdraw {
  border-left-color: #f87171;
}

.cashflow-date {
  font-size: 0.75rem;
  color: rgba(74, 222, 128, 0.6);
  font-weight: 500;
  letter-spacing: 1px;
}

.cashflow-type {
  font-size: 0.9rem;
  font-weight: 500;
  color: #4ade80;
  text-transform: uppercase;
}

.cashflow-amount {
  font-size: 1.1rem;
  font-weight: 500;
  letter-spacing: 1px;
}

.cashflow-item.deposit .cashflow-amount {
  color: #22c55e;
}

.cashflow-item.withdraw .cashflow-amount {
  color: #f87171;
}

@media (max-width: 768px) {
  .cashflow-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
</style>


