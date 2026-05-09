<template>
  <span class="status-pulse" :class="[status, size]" :title="label" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ status: 'running' | 'success' | 'warning' | 'danger' | 'idle'; size?: 'sm' | 'md' | 'lg' }>()
const label = computed(() => ({ running: '运行中', success: '正常', warning: '警告', danger: '异常', idle: '空闲' }[props.status]))
</script>

<style scoped>
.status-pulse { display: inline-block; border-radius: 50%; }
.status-pulse.sm { width: 8px; height: 8px; }
.status-pulse.md { width: 10px; height: 10px; }
.status-pulse.lg { width: 14px; height: 14px; }
.status-pulse.running { background: var(--status-running); animation: pulse-glow 2s ease-in-out infinite; }
.status-pulse.success { background: var(--status-success); }
.status-pulse.warning { background: var(--status-warning); animation: pulse-dot 1.5s ease-in-out infinite; }
.status-pulse.danger { background: var(--status-danger); animation: pulse-dot 1s ease-in-out infinite; }
.status-pulse.idle { background: var(--color-soft); }
</style>
