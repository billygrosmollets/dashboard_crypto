<template>
  <div class="metric-card">
    <div class="card-header">
      {{ period.label }}
    </div>
    <div class="card-body">
      <div class="metric-item">
        <span class="metric-label">TWR</span>
        <span class="metric-value" :class="twrClass">{{ twrValue }}</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">PnL</span>
        <span class="metric-value" :class="pnlDollarClass">{{ pnlDollarValue }}</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">PnL %</span>
        <span class="metric-value" :class="pnlPercentClass">{{ pnlPercentValue }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFormatting } from '@/composables/useFormatting'

const { formatNumber } = useFormatting()

const props = defineProps({
  period: {
    type: Object,
    required: true
  },
  data: {
    type: Object,
    default: null
  }
})

const twrValue = computed(() => {
  if (!props.data || props.data.twr_percent === null || props.data.twr_percent === undefined) {
    return 'N/A'
  }
  const val = props.data.twr_percent
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
})

const pnlDollarValue = computed(() => {
  if (!props.data || props.data.total_pnl === null || props.data.total_pnl === undefined) {
    return 'N/A'
  }
  const val = props.data.total_pnl
  return `$${formatNumber(Math.abs(val))}`
})

const pnlPercentValue = computed(() => {
  if (!props.data || props.data.pnl_percent === null || props.data.pnl_percent === undefined) {
    return 'N/A'
  }
  const val = props.data.pnl_percent
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
})

const twrClass = computed(() => {
  if (!props.data || props.data.twr_percent === null || props.data.twr_percent === undefined) {
    return 'neutral'
  }
  return props.data.twr_percent >= 0 ? 'positive' : 'negative'
})

const pnlDollarClass = computed(() => {
  if (!props.data || props.data.total_pnl === null || props.data.total_pnl === undefined) {
    return 'neutral'
  }
  return props.data.total_pnl >= 0 ? 'positive' : 'negative'
})

const pnlPercentClass = computed(() => {
  if (!props.data || props.data.pnl_percent === null || props.data.pnl_percent === undefined) {
    return 'neutral'
  }
  return props.data.pnl_percent >= 0 ? 'positive' : 'negative'
})
</script>

<style scoped>
.metric-card {
  background: var(--bg-primary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.5rem;
  padding: 1rem;
  font-family: inherit;
}

.card-header {
  color: #4ade80;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metric-label {
  color: rgba(74, 222, 128, 0.6);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-weight: 500;
}

.metric-value.positive {
  color: #4ade80;
}

.metric-value.negative {
  color: #f87171;
}

.metric-value.neutral {
  color: #4ade80;
}
</style>
