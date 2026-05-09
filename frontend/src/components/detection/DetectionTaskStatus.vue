<template>
  <el-card shadow="never">
    <template #header><span style="font-weight:700;">任务状态</span></template>
    <div class="task-status-bar" style="margin-top:0;">
      <span class="status-dot" :class="statusClass"></span>
      <strong>{{ statusText }}</strong>
      <span style="font-size:12px;color:var(--color-muted);">进度 {{ progress }}%</span>
    </div>
    <el-progress v-if="progress > 0" :percentage="progress" :stroke-width="10" style="margin-top:12px;" />
    <div v-if="error" class="error-text" style="margin-top:10px;">{{ error }}</div>
    <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
      <el-button v-for="action in availableActions" :key="action.key" size="small"
        :type="action.type || ''" :loading="actionLoading === action.key"
        :disabled="!action.enabled" @click="$emit('control', action.key)">
        {{ action.label }}
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  status: string
  progress?: number
  error?: string
  availableActions?: Array<{ key: string; label: string; type?: string; enabled: boolean }>
  actionLoading?: string
}>(), {
  progress: 0,
  error: '',
  availableActions: () => [],
  actionLoading: '',
})

defineEmits<{ control: [key: string] }>()

const statusClass = computed(() => {
  if (props.status === 'running') return 'running'
  if (props.status === 'done') return 'success'
  if (props.status === 'failed') return 'failed'
  return 'idle'
})
const statusText = computed(() => {
  const map: Record<string, string> = { pending: '等待中', running: '检测中', paused: '已暂停', cancelled: '已取消', done: '已完成', failed: '失败' }
  return map[props.status] || props.status
})
</script>
