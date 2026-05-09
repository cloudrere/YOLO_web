<template>
  <div class="motion-panel" :class="[effect]">
    <slot />
    <div v-if="effect === 'shimmer'" class="shimmer-sweep" />
    <div v-if="effect === 'glow'" class="glow-border" />
  </div>
</template>

<script setup lang="ts">
defineProps<{ effect?: 'shimmer' | 'glow' | 'none' }>()
</script>

<style scoped>
.motion-panel { position: relative; overflow: hidden; border-radius: var(--radius-md); transition: transform var(--motion-fast) var(--ease-standard), box-shadow var(--motion-fast) var(--ease-standard); }
.motion-panel.shimmer:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.motion-panel.glow:hover { box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
.shimmer-sweep { position: absolute; inset: 0; pointer-events: none; opacity: 0; transition: opacity var(--motion-fast); background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.5) 45%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0.5) 55%, transparent 60%); background-size: 200% 100%; }
.motion-panel:hover .shimmer-sweep { opacity: 1; animation: shimmer 1s var(--ease-standard) forwards; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.glow-border { position: absolute; inset: -1px; border-radius: inherit; pointer-events: none; border: 2px solid transparent; transition: border-color var(--motion-fast); }
.motion-panel.glow:hover .glow-border { border-color: var(--color-primary); }
</style>
