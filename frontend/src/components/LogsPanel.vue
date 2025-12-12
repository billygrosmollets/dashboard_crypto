<template>
  <div class="logs-panel">
    <div class="logs-header">
      <h3>Logs d'Exécution</h3>
      <button @click="clearLogs" class="btn-clear">Effacer</button>
    </div>

    <div class="logs-container">
      <div
        v-for="(log, index) in logs"
        :key="index"
        class="log-entry"
        :class="log.type"
      >
        <span class="timestamp">{{ log.timestamp }}</span>
        <span class="message">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['clear'])

function clearLogs() {
  emit('clear')
}
</script>

<style scoped>
/* Glassmorphism Logs Panel */
.logs-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px var(--glass-shadow);
  margin-top: 2rem;
  position: relative;
  overflow: hidden;
}

.logs-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold-primary), transparent);
  opacity: 0.2;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--glass-border);
}

.logs-header h3 {
  color: var(--gray-800);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.5px;
}

.btn-clear {
  padding: 10px 20px;
  background: rgba(117, 117, 117, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  color: var(--gray-600);
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-clear:hover {
  background: rgba(117, 117, 117, 0.5);
  color: var(--gray-700);
  transform: translateY(-2px);
}

/* Terminal-style Container */
.logs-container {
  background: rgba(10, 10, 10, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(212, 175, 55, 0.1);
  border-radius: 12px;
  padding: 1.25rem;
  max-height: 450px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  position: relative;
}

.logs-container::before {
  content: '> Terminal Output';
  position: absolute;
  top: -0.5rem;
  left: 1rem;
  font-size: 0.7rem;
  color: var(--gold-primary);
  background: var(--bg-primary);
  padding: 0 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}

.log-entry {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(212, 175, 55, 0.05);
  transition: all 0.2s ease;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry:hover {
  background: rgba(212, 175, 55, 0.03);
  padding-left: 0.5rem;
  margin-left: -0.5rem;
  border-radius: 6px;
}

.timestamp {
  color: var(--gray-500);
  font-size: 0.75rem;
  min-width: 90px;
  flex-shrink: 0;
  font-weight: 600;
}

.message {
  color: var(--gray-600);
  white-space: pre-wrap;
  word-break: break-word;
  font-weight: 500;
}

.log-entry.info .timestamp {
  color: var(--info);
}

.log-entry.info .message {
  color: var(--info);
}

.log-entry.success .timestamp {
  color: var(--success);
}

.log-entry.success .message {
  color: var(--success);
  font-weight: 600;
}

.log-entry.error .timestamp {
  color: var(--error);
}

.log-entry.error .message {
  color: var(--error);
  font-weight: 600;
}

.log-entry.warning .timestamp {
  color: var(--warning);
}

.log-entry.warning .message {
  color: var(--warning);
  font-weight: 600;
}

/* Custom scrollbar */
.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(28, 28, 28, 0.3);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--gold-dark), var(--gold-primary));
  border-radius: 4px;
  border: 2px solid rgba(28, 28, 28, 0.3);
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--gold-primary), var(--gold-secondary));
}
</style>
