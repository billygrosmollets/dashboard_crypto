/**
 * HTTP Polling Composable
 * Executes a callback function at regular intervals
 * Matches the 60-second auto-refresh pattern from the original Tkinter app
 */
import { onMounted, onUnmounted } from 'vue'

export function usePolling(callback, interval = 60000) {
  let timerId = null

  onMounted(() => {
    // Execute immediately on mount
    callback()

    // Then execute at regular intervals
    timerId = setInterval(callback, interval)
  })

  onUnmounted(() => {
    if (timerId) {
      clearInterval(timerId)
    }
  })

  return {
    // Could expose methods to pause/resume polling if needed
  }
}
