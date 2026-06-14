<script setup lang="ts">
const props = defineProps<{
  data: { time: string; value: number }[]
}>()

const svgWidth = 600
const svgHeight = 80
const padding = { top: 4, right: 8, bottom: 20, left: 8 }
const chartW = svgWidth - padding.left - padding.right
const chartH = svgHeight - padding.top - padding.bottom

const maxVal = computed(() => Math.max(...props.data.map(d => d.value), 1))

const bars = computed(() => {
  return props.data.map((d, i) => {
    const x = padding.left + (i / props.data.length) * chartW
    const w = Math.max(chartW / props.data.length - 2, 2)
    const h = (d.value / maxVal.value) * chartH
    return { x, y: padding.top + chartH - h, w, h, time: d.time, value: d.value }
  })
})
</script>

<template>
  <div class="timeline-chart">
    <div class="chart-header">
      <span class="chart-title">Request Timeline</span>
    </div>
    <div class="chart-body">
      <svg v-if="data.length > 0" :viewBox="`0 0 ${svgWidth} ${svgHeight}`" class="chart-svg">
        <rect
          v-for="b in bars"
          :key="b.time"
          :x="b.x"
          :y="b.y"
          :width="b.w"
          :height="b.h"
          rx="2"
          fill="var(--accent)"
          opacity="0.7"
        >
          <title>{{ b.time }} — {{ b.value }} req</title>
        </rect>
      </svg>
      <div v-else class="chart-empty">
        Waiting for data…
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-chart {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}

.chart-header {
  margin-bottom: 12px;
}

.chart-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-body {
  overflow-x: auto;
}

.chart-svg {
  display: block;
  width: 100%;
  height: auto;
}

.chart-empty {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 16px 0;
  text-align: center;
}
</style>
