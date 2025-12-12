/**
 * API Wrapper Composable
 * Provides centralized error handling and axios configuration
 */
import axios from 'axios'

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: '/api', // Proxied to Flask backend via Vite
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export function useAPI() {
  return {
    client: apiClient,

    // Convenience methods
    async get(url, config) {
      const response = await apiClient.get(url, config)
      return response.data
    },

    async post(url, data, config) {
      const response = await apiClient.post(url, data, config)
      return response.data
    },

    async put(url, data, config) {
      const response = await apiClient.put(url, data, config)
      return response.data
    },

    async delete(url, config) {
      const response = await apiClient.delete(url, config)
      return response.data
    }
  }
}
