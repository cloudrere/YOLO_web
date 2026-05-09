<template>
  <span class="animated-number">{{ displayValue }}</span>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
const props = defineProps<{ value: number; duration?: number }>()
const displayValue = ref(0)

function animate(from: number, to: number) {
  const dur = props.duration || 800
  const start = performance.now()
  function tick(now: number) {
    const elapsed = now - start
    const progress = Math.min(elapsed / dur, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayValue.value = Math.round(from + (to - from) * eased)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

onMounted(() => { displayValue.value = props.value })
watch(() => props.value, (next, prev) => { animate(prev || 0, next) })
</script>

<style scoped>
.animated-number { font-variant-numeric: tabular-nums; }
</style>
