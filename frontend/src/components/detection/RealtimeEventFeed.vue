<template>
  <div class="event-feed" ref="feedEl">
    <TransitionGroup name="list">
      <div v-for="ev in events" :key="ev.id" class="event-item">
        <span class="event-time">{{ ev.time }}</span>
        <span class="event-label">{{ ev.label }}</span>
        <span v-if="ev.detail" style="display:block;color:var(--color-muted);font-size:12px;margin-top:2px;">{{ ev.detail }}</span>
      </div>
    </TransitionGroup>
    <el-empty v-if="!events.length" description="等待实时识别事件" />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  events: Array<{ id: number; time: string; label: string; detail?: string }>
}>()
</script>
