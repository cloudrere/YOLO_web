<template>
  <div class="queue-list">
    <TransitionGroup name="list">
      <div v-for="item in items" :key="item.name" class="queue-item" :class="item.status">
        <StatusPulse :status="statusType(item.status)" size="sm" />
        <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;">{{ item.name }}</span>
        <el-tag size="small" :type="item.status === 'done' ? 'success' : item.status === 'failed' ? 'danger' : item.status === 'running' ? 'warning' : 'info'">
          {{ statusLabel(item.status) }}
        </el-tag>
      </div>
    </TransitionGroup>
    <el-empty v-if="!items.length" description="等待添加检测文件" />
  </div>
</template>

<script setup lang="ts">
import StatusPulse from '../common/StatusPulse.vue'

defineProps<{
  items: Array<{ name: string; status: 'pending' | 'running' | 'done' | 'failed' }>
}>()

function statusType(s: string) {
  return s === 'running' ? 'running' : s === 'done' ? 'success' : s === 'failed' ? 'danger' : 'idle'
}
function statusLabel(s: string) {
  return { pending: '等待', running: '检测中', done: '完成', failed: '失败' }[s] || s
}
</script>
