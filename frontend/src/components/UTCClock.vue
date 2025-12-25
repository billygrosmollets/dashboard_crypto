<template>
  <div class="utc-clock">
    <span class="clock-label">UTC:</span>
    <span class="clock-time">{{ utcTime }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const utcTime = ref('')
let intervalId = null

function updateTime() {
  const now = new Date()
  utcTime.value = now.toISOString().substring(11, 19) // HH:MM:SS
}

onMounted(() => {
  updateTime()
  intervalId = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
.utc-clock {
  font-family: inherit;
  color: #4ade80;
  font-weight: 500;
  letter-spacing: 1px;
  font-size: 1rem;
}

.clock-label {
  color: rgba(74, 222, 128, 0.6);
  margin-right: 0.5rem;
}

.clock-time {
  color: #4ade80;
}
</style>
