<template>
  <div class="detect-box-overlay">
    <div
      v-for="(box, i) in boxes" :key="i"
      class="detect-box"
      :style="{ left: box.x + '%', top: box.y + '%', width: box.w + '%', height: box.h + '%', animationDelay: i * 80 + 'ms' }"
    >
      <span class="box-label">{{ box.label }} {{ (box.confidence * 100).toFixed(0) }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ boxes: Array<{ x: number; y: number; w: number; h: number; label: string; confidence: number }> }>()
</script>
