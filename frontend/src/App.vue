<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>
</template>

<script setup>
</script>

<style>
/* Terminal Theme - Matrix Green */
:root {
  /* Backgrounds */
  --bg-primary: #0a0a0a;
  --bg-secondary: #000000;
  --bg-tertiary: #0f0f0f;

  /* Terminal Green Palette */
  --terminal-green: #00ff41;
  --terminal-green-bright: #00ff00;
  --terminal-green-dim: #00cc33;
  --terminal-green-dark: #008822;

  /* Status Colors */
  --success: #00ff00;
  --error: #ff0000;
  --warning: #ffff00;
  --info: #00ffff;

  /* Gray Scale */
  --gray-100: #1a1a1a;
  --gray-200: #2a2a2a;
  --gray-300: #333333;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Courier New', Consolas, Monaco, 'Lucida Console', monospace;
  background: var(--bg-primary);
  color: var(--terminal-green);
  line-height: 1.5;
}

#app {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Terminal Scrollbar */
::-webkit-scrollbar {
  width: 12px;
  background: var(--bg-primary);
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border: 1px solid var(--terminal-green-dark);
}

::-webkit-scrollbar-thumb {
  background: var(--terminal-green-dim);
  border: 1px solid var(--terminal-green);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--terminal-green);
}

/* Terminal Modal Styling */
dialog.terminal-modal {
  background: var(--bg-primary);
  border: 3px solid var(--terminal-green-bright);
  color: var(--terminal-green);
  padding: 0;
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  font-family: inherit;
  margin: auto;
  top: 50%;
  transform: translateY(-50%);
}

dialog.terminal-modal::backdrop {
  background: rgba(0, 0, 0, 0.85);
}

dialog.cashflow-modal {
  max-height: 70vh;
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--terminal-green);
  position: sticky;
  top: 0;
  z-index: 10;
}

.modal-header h2 {
  color: var(--terminal-green-bright);
  text-transform: uppercase;
  letter-spacing: 2px;
  font-size: 1.2rem;
  margin: 0;
  font-weight: bold;
}

.close-btn {
  background: transparent;
  border: 2px solid var(--error);
  color: var(--error);
  font-family: inherit;
  font-weight: bold;
  padding: 0.25rem 0.75rem;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--error);
  color: var(--bg-primary);
}
</style>
