<template>
  <div class="empty-detect-canvas">
    <div class="scan-overlay"><div class="scan-line" /></div>
    <div class="placeholder-content">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none" style="opacity:0.3;">
        <rect x="8" y="8" width="48" height="48" rx="4" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4" />
        <rect x="20" y="20" width="24" height="16" rx="2" stroke="currentColor" stroke-width="1.5" />
        <circle cx="32" cy="28" r="4" stroke="currentColor" stroke-width="1.5" />
      </svg>
      <strong>{{ title }}</strong>
      <span>{{ desc }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title?: string; desc?: string }>()
</script>
