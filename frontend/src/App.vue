<template>
  <div id="app">
    <header class="app-header">
      <h1>🚀 Binance Portfolio Manager</h1>
      <div class="connection-status" :class="{ connected: isConnected }">
        {{ isConnected ? 'Connecté' : 'Déconnecté' }}
      </div>
    </header>

    <div class="app-content">
      <nav class="sidebar">
        <ul>
          <li>
            <router-link to="/">Portfolio</router-link>
          </li>
          <li>
            <router-link to="/analytics">TWR Analytics</router-link>
          </li>
          <!-- More navigation items will be added in later phases (Rebalancing, Converter) -->
        </ul>
      </nav>

      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const isConnected = ref(false)

// Check connection status on mount
onMounted(async () => {
  try {
    const response = await axios.get('/api/portfolio/connection/test')
    isConnected.value = response.data.connected
  } catch (error) {
    console.error('Connection test failed:', error)
    isConnected.value = false
  }
})
</script>

<style>
/* Dark Pro Color Palette */
:root {
  --bg-primary: #0a0a0a;
  --bg-secondary: #141414;
  --bg-tertiary: #1c1c1c;

  --glass-bg: rgba(28, 28, 28, 0.7);
  --glass-border: rgba(255, 215, 0, 0.15);
  --glass-shadow: rgba(0, 0, 0, 0.5);

  --gold-primary: #d4af37;
  --gold-secondary: #f0d26f;
  --gold-dark: #b8941f;

  --gray-100: #2a2a2a;
  --gray-200: #383838;
  --gray-300: #4a4a4a;
  --gray-400: #666666;
  --gray-500: #888888;
  --gray-600: #b0b0b0;
  --gray-700: #c0c0c0;
  --gray-800: #d0d0d0;

  --success: #4caf50;
  --error: #ef5350;
  --warning: #ff9800;
  --info: #42a5f5;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Lexend', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg-primary);
  color: var(--gray-700);
  background-image:
    radial-gradient(at 0% 0%, rgba(212, 175, 55, 0.02) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(212, 175, 55, 0.01) 0px, transparent 50%);
  background-attachment: fixed;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Glassmorphism Header */
.app-header {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--glass-border);
  color: var(--gray-800);
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px var(--glass-shadow);
  position: sticky;
  top: 0;
  z-index: 100;
}

.app-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--gold-secondary), var(--gold-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.connection-status {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  color: var(--error);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.connection-status.connected {
  color: var(--success);
  border-color: rgba(76, 175, 80, 0.3);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
}

.app-content {
  flex: 1;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 0;
}

/* Glassmorphism Sidebar */
.sidebar {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--glass-border);
  padding: 2rem 0;
  box-shadow: 4px 0 20px var(--glass-shadow);
}

.sidebar ul {
  list-style: none;
}

.sidebar li {
  margin: 0;
}

.sidebar a {
  display: block;
  color: var(--gray-600);
  text-decoration: none;
  padding: 1rem 2rem;
  margin: 0.25rem 1rem;
  border-radius: 10px;
  transition: all 0.3s ease;
  position: relative;
  font-weight: 500;
}

.sidebar a::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 10px;
  padding: 1px;
  background: linear-gradient(135deg, transparent, var(--glass-border));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sidebar a:hover {
  background: rgba(212, 175, 55, 0.08);
  color: var(--gold-secondary);
}

.sidebar a:hover::before {
  opacity: 1;
}

.sidebar a.router-link-active {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.08));
  color: var(--gold-primary);
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.sidebar a.router-link-active::before {
  opacity: 1;
  background: linear-gradient(135deg, var(--gold-primary), transparent);
}

.main-content {
  padding: 2rem;
  overflow-y: auto;
  background: transparent;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--gold-dark), var(--gold-primary));
  border-radius: 5px;
  border: 2px solid var(--bg-secondary);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--gold-primary), var(--gold-secondary));
}
</style>
