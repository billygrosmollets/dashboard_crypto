/**
 * useFormatting - Composable for number and date formatting
 * Shared formatting utilities across the application
 */

export function useFormatting() {
  /**
   * Format a number with French locale
   * @param {number|null|undefined} value - The number to format
   * @returns {string} Formatted number string
   */
  function formatNumber(value) {
    if (value === null || value === undefined) return '0.00'
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  /**
   * Format a timestamp to French locale date/time
   * @param {string|Date} timestamp - The timestamp to format
   * @returns {string} Formatted date string
   */
  function formatDate(timestamp) {
    return new Date(timestamp).toLocaleString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return {
    formatNumber,
    formatDate
  }
}
