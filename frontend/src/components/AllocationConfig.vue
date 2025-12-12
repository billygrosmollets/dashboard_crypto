<template>
  <div class="allocation-config">
    <h3>Configuration d'Allocation par Asset</h3>
    <p class="description">
      Configurez la répartition cible pour chaque asset représentant au moins 1% de votre portfolio.
      Le total doit être égal à 100%.
    </p>

    <div v-if="loading" class="loading">
      Chargement...
    </div>

    <div v-else class="allocation-form">
      <div class="current-vs-target">
        <div class="column">
          <h4>Allocation Actuelle</h4>
          <div class="asset-list">
            <div
              v-for="asset in significantAssets"
              :key="asset"
              class="asset-row current"
            >
              <span class="asset-name">{{ asset }}</span>
              <span class="asset-value">{{ formatPercent(currentPercentages[asset] || 0) }}</span>
            </div>
          </div>
        </div>

        <div class="column">
          <h4>Allocation Cible</h4>
          <div class="asset-list">
            <div
              v-for="asset in significantAssets"
              :key="asset"
              class="asset-row target"
            >
              <label :for="`alloc-${asset}`" class="asset-name">{{ asset }}</label>
              <div class="input-group">
                <input
                  :id="`alloc-${asset}`"
                  type="number"
                  v-model.number="formData[asset]"
                  step="0.1"
                  min="0"
                  max="100"
                  @input="validateTotal"
                />
                <span class="unit">%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="total-display" :class="{ valid: isValid, invalid: !isValid }">
        <span class="label">Total:</span>
        <span class="value">{{ formatPercent(total) }}</span>
        <span v-if="!isValid" class="error-text">⚠️ Doit être égal à 100%</span>
        <span v-else class="success-text">✅</span>
      </div>

      <div class="form-actions">
        <button
          @click="autoAdjust"
          class="btn-auto"
          :disabled="loading"
        >
          ⚡ Auto-ajuster au total actuel
        </button>

        <button
          @click="saveAllocation"
          class="btn-save"
          :disabled="!isValid || loading"
        >
          {{ loading ? 'Sauvegarde...' : '💾 Sauvegarder' }}
        </button>

        <button
          @click="resetForm"
          class="btn-reset"
          :disabled="loading"
        >
          🔄 Réinitialiser
        </button>
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAPI } from '@/composables/useAPI'

const api = useAPI()

const loading = ref(false)
const significantAssets = ref([])
const currentPercentages = ref({})
const formData = ref({})
const successMessage = ref('')
const errorMessage = ref('')

const total = computed(() => {
  return Object.values(formData.value).reduce((sum, val) => sum + (parseFloat(val) || 0), 0)
})

const isValid = computed(() => {
  return Math.abs(total.value - 100) < 0.01
})

onMounted(async () => {
  await loadAllocationData()
})

async function loadAllocationData() {
  loading.value = true
  errorMessage.value = ''

  try {
    const data = await api.get('/rebalancing/allocation')

    significantAssets.value = data.significant_assets || []
    currentPercentages.value = data.current_percentages || {}

    // Initialize form with saved allocations or current percentages
    const savedAllocations = data.allocations || {}
    formData.value = {}

    significantAssets.value.forEach(asset => {
      formData.value[asset] = savedAllocations[asset] || currentPercentages.value[asset] || 0
    })

  } catch (error) {
    errorMessage.value = error.message || 'Erreur lors du chargement'
    console.error('Error loading allocation:', error)
  } finally {
    loading.value = false
  }
}

function validateTotal() {
  // Just trigger reactivity
}

function autoAdjust() {
  // Auto-adjust to use current percentages
  formData.value = { ...currentPercentages.value }
}

async function saveAllocation() {
  if (!isValid.value) {
    errorMessage.value = 'Le total doit être égal à 100%'
    return
  }

  loading.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await api.post('/rebalancing/allocation', {
      allocations: formData.value
    })

    successMessage.value = 'Allocation sauvegardée avec succès !'

    // Clear message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    errorMessage.value = error.message || 'Erreur lors de la sauvegarde'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  loadAllocationData()
  errorMessage.value = ''
  successMessage.value = ''
}

function formatPercent(value) {
  return `${value.toFixed(2)}%`
}
</script>

<style scoped>
.allocation-config {
  padding: 20px;
}

h3 {
  margin-bottom: 10px;
  color: #e0e0e0;
  font-size: 24px;
}

.description {
  margin-bottom: 20px;
  color: #b0b0b0;
  font-size: 14px;
  line-height: 1.5;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #888;
}

.allocation-form {
  background: #2a2a2a;
  padding: 20px;
  border-radius: 8px;
}

.current-vs-target {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 20px;
}

.column h4 {
  margin-bottom: 15px;
  color: #e0e0e0;
  font-size: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #444;
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.asset-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #1a1a1a;
  border-radius: 4px;
}

.asset-row.current {
  border-left: 3px solid #2196f3;
}

.asset-row.target {
  border-left: 3px solid #4caf50;
}

.asset-name {
  font-weight: 600;
  color: #e0e0e0;
  font-size: 14px;
}

.asset-value {
  color: #b0b0b0;
  font-size: 14px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

input[type="number"] {
  width: 80px;
  padding: 6px 10px;
  background: #0a0a0a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 14px;
  text-align: right;
}

input[type="number"]:focus {
  outline: none;
  border-color: #4caf50;
}

.unit {
  color: #888;
  font-size: 14px;
}

.total-display {
  padding: 15px 20px;
  border-radius: 6px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.total-display.valid {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 2px solid #4caf50;
}

.total-display.invalid {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 2px solid #ff6b6b;
}

.error-text,
.success-text {
  font-size: 16px;
}

.form-actions {
  display: flex;
  gap: 10px;
}

button {
  padding: 12px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-auto {
  background: #2196f3;
  color: white;
}

.btn-auto:hover:not(:disabled) {
  background: #1976d2;
}

.btn-save {
  background: #4caf50;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #45a049;
}

.btn-reset {
  background: #757575;
  color: white;
}

.btn-reset:hover:not(:disabled) {
  background: #616161;
}

.success-message,
.error-message {
  margin-top: 15px;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
}

.success-message {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid #4caf50;
}

.error-message {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
}

@media (max-width: 768px) {
  .current-vs-target {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
