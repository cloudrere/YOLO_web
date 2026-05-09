<template>
  <div class="timeline">
    <div v-for="(task, i) in tasks" :key="i" class="timeline-item" :style="{ animationDelay: i * 50 + 'ms' }">
      <StatusPulse :status="task.status" size="sm" />
      <div class="timeline-content">
        <strong>{{ task.title }}</strong>
        <span>{{ task.time }}</span>
      </div>
      <el-tag v-if="task.tag" size="small" :type="task.tagType || 'info'">{{ task.tag }}</el-tag>
    </div>
    <el-empty v-if="!tasks.length" description="暂无检测任务" />
  </div>
</template>

<script setup lang="ts">
import StatusPulse from '../common/StatusPulse.vue'

defineProps<{
  tasks: Array<{
    title: string
    time: string
    status: 'running' | 'success' | 'warning' | 'danger' | 'idle'
    tag?: string
    tagType?: string
  }>
}>()
</script>

<style scoped>
.timeline { display: grid; gap: 4px; }
.timeline-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--color-bg); border: 1px solid var(--color-border); animation: slide-up-fade var(--motion-normal) var(--ease-emphasized) both; }
.timeline-content strong { display: block; font-size: 13px; color: var(--color-ink); }
.timeline-content span { display: block; font-size: 11px; color: var(--color-soft); margin-top: 2px; }
</style>
