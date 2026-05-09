<template>
  <div class="progress-ring" :style="{ width: pxSize, height: pxSize }">
    <svg :width="pxSize" :height="pxSize" viewBox="0 0 100 100">
      <circle class="ring-bg" cx="50" cy="50" :r="radius" :stroke-width="stroke" />
      <circle class="ring-fill" cx="50" cy="50" :r="radius" :stroke-width="stroke" :stroke-dasharray="circumference" :stroke-dashoffset="dashOffset" :stroke="color" />
    </svg>
    <span class="ring-text" :style="{ fontSize: textSize }">{{ displayText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ percent: number; status?: string; size?: number }>()
const pxSize = computed(() => `${props.size || 80}px`)
const radius = 40
const stroke = 8
const circumference = 2 * Math.PI * radius
const dashOffset = computed(() => circumference * (1 - Math.min(Math.max(props.percent, 0), 100) / 100))
const color = computed(() => {
  const s = props.status || ''
  if (s === 'running') return 'var(--status-running)'
  if (s === 'done' || s === 'success') return 'var(--status-success)'
  if (s === 'failed') return 'var(--status-danger)'
  return 'var(--color-primary)'
})
const displayText = computed(() => `${Math.round(props.percent)}%`)
const textSize = computed(() => `${(props.size || 80) * 0.18}px`)
</script>

<style scoped>
.progress-ring { display: inline-grid; place-items: center; position: relative; }
.progress-ring svg { transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: var(--color-border); }
.ring-fill { fill: none; stroke-linecap: round; transition: stroke-dashoffset var(--motion-slow) var(--ease-standard); }
.ring-text { position: absolute; font-weight: 800; color: var(--color-ink); }
</style>
