<template>
  <div class="twr-chart-container">
    <div class="chart-header">
      <h3>&gt; Time-Weighted Return</h3>
      <div class="chart-controls">
        <button
          v-for="period in periods"
          :key="period.days"
          @click="selectedPeriod = period.days"
          :class="['period-btn', { active: selectedPeriod === period.days }]"
        >
          {{ period.label }}
        </button>
      </div>
    </div>
    <div class="chart-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import 'chartjs-adapter-date-fns'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

const chartCanvas = ref(null)
let chartInstance = null

const selectedPeriod = ref(30)
const periods = [
  { days: 7, label: '7D' },
  { days: 30, label: '30D' },
  { days: 90, label: '90D' },
  { days: 180, label: '180D' },
  { days: 365, label: '1Y' },
  { days: 0, label: 'ALL' }
]

// Fetch TWR history from backend
async function fetchTWRHistory(days) {
  try {
    const response = await fetch(`/api/performance/twr-history?days=${days}`)
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching TWR history:', error)
    return []
  }
}

function createChart(data) {
  if (chartInstance) {
    chartInstance.destroy()
  }

  if (!chartCanvas.value) return

  const ctx = chartCanvas.value.getContext('2d')

  // Calculate time range: use actual data points as references
  let maxTime, minTime, customTicks
  if (data.length > 0) {
    // Use the ACTUAL first and last data points as boundaries
    const firstTimestamp = new Date(data[0].x)
    const lastTimestamp = new Date(data[data.length - 1].x)

    maxTime = lastTimestamp.getTime()
    minTime = firstTimestamp.getTime()

    // Generate exactly 11 evenly spaced ticks (0 to 10 = 10 intervals)
    customTicks = []
    const tickInterval = (maxTime - minTime) / 10
    for (let i = 0; i <= 10; i++) {
      customTicks.push(minTime + (i * tickInterval))
    }
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'TWR (%)',
        data: data,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.05)',
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointBackgroundColor: '#22c55e',
        pointBorderColor: '#22c55e',
        pointHoverBackgroundColor: '#22c55e',
        pointHoverBorderColor: '#22c55e'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#000000',
          borderColor: '#22c55e',
          borderWidth: 1,
          titleColor: '#4ade80',
          bodyColor: '#4ade80',
          titleFont: {
            family: "'Courier New', Consolas, Monaco, monospace",
            size: 12
          },
          bodyFont: {
            family: "'Courier New', Consolas, Monaco, monospace",
            size: 11
          },
          padding: 8,
          displayColors: false,
          borderRadius: 8,
          callbacks: {
            label: function(context) {
              return `${context.parsed.y >= 0 ? '+' : ''}${context.parsed.y.toFixed(2)}%`
            }
          }
        }
      },
      scales: {
        x: {
          type: 'time',
          min: minTime,
          max: maxTime,
          time: {
            displayFormats: {
              hour: 'dd MMM',
              day: 'dd MMM',
              week: 'dd MMM',
              month: 'dd MMM',
              quarter: 'dd MMM',
              year: 'dd MMM'
            }
          },
          grid: {
            color: 'rgba(74, 222, 128, 0.15)',
            lineWidth: 1,
            drawBorder: true,
            borderDash: [3, 3]
          },
          ticks: {
            color: '#4ade80',
            font: {
              family: "'Courier New', Consolas, Monaco, monospace",
              size: 12,
              weight: 'bold'
            },
            maxRotation: 0,
            minRotation: 0,
            autoSkip: false,
            callback: function(value, index, ticks) {
              const date = new Date(value)
              const day = date.getDate().toString().padStart(2, '0')
              const month = date.toLocaleString('en', { month: 'short' })
              const year = date.getFullYear()
              const hours = date.getHours().toString().padStart(2, '0')
              const minutes = date.getMinutes().toString().padStart(2, '0')

              // First and last tick: show date + year + time
              if (index === 0 || index === ticks.length - 1) {
                return `${day} ${month} ${year} ${hours}:${minutes}`
              }

              // Middle ticks: show date + time (no year)
              return `${day} ${month} ${hours}:${minutes}`
            }
          },
          afterBuildTicks: function(axis) {
            // Override ticks with exactly 10 evenly spaced values
            if (customTicks) {
              axis.ticks = customTicks.map(value => ({ value }))
            }
          },
          border: {
            display: true,
            color: '#4ade80',
            width: 2
          }
        },
        y: {
          grid: {
            color: 'rgba(74, 222, 128, 0.15)',
            lineWidth: 1,
            drawBorder: true,
            borderDash: [3, 3]
          },
          ticks: {
            color: '#4ade80',
            font: {
              family: "'Courier New', Consolas, Monaco, monospace",
              size: 12,
              weight: 'bold'
            },
            callback: function(value) {
              return value.toFixed(0) + '%'
            }
          },
          border: {
            display: true,
            color: '#4ade80',
            width: 2
          }
        }
      }
    }
  })
}

async function updateChart() {
  const data = await fetchTWRHistory(selectedPeriod.value)
  createChart(data)
}

watch(selectedPeriod, () => {
  updateChart()
})

onMounted(() => {
  updateChart()
})
</script>

<style scoped>
.twr-chart-container {
  background: var(--bg-primary);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.75rem;
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.chart-header h3 {
  color: #4ade80;
  font-size: 1rem;
  font-weight: 500;
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: 0.5rem;
}

.period-btn {
  background: var(--bg-primary);
  color: rgba(34, 197, 94, 0.6);
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 0.25rem 0.75rem;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.period-btn:hover {
  border-color: #22c55e;
  color: #4ade80;
}

.period-btn.active {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border-color: #22c55e;
}

.chart-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
}

.chart-wrapper canvas {
  max-height: 100%;
}
</style>
