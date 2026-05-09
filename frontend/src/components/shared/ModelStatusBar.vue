<template>
  <div class="model-status-bar">
    <span style="font-size:11px;color:var(--color-muted);font-weight:600;">当前推理模型</span>
    <strong class="model-name">{{ displayName }}</strong>
    <span class="model-device">{{ deviceLabel }}</span>
    <el-tag v-if="warmupStatus" :type="warmupTagType" size="small">{{ warmupText }}</el-tag>
    <span v-if="active?.cuda_available" style="font-size:11px;color:var(--color-muted);">{{ active.cuda_name || 'CUDA 可用' }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { activeModel } from '@/api/model'
import type { ModelEngineState } from '@/api/types'

const active = ref<ModelEngineState | null>(null)

const displayName = computed(() => active.value?.active_model?.display_name || active.value?.active_model?.name || '未激活模型')
const deviceLabel = computed(() => {
  const d = active.value?.device || active.value?.requested_device || 'auto'
  if (!d || d === 'auto') return '自动'
  if (d === 'cpu') return 'CPU'
  if (d.startsWith('cuda')) return 'GPU'
  return d
})
const warmupStatus = computed(() => active.value?.warmup_status)
const warmupText = computed(() => {
  const map: Record<string, string> = { cuda_ready: 'GPU 就绪', cpu_ready: 'CPU 就绪', pending: '预热中', failed: '预热失败', not_loaded: '未加载', idle: '待初始化' }
  return map[active.value?.warmup_status || ''] || active.value?.warmup_status || ''
})
const warmupTagType = computed(() => {
  const s = active.value?.warmup_status || ''
  if (s === 'cuda_ready' || s === 'cpu_ready') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'pending') return 'warning'
  return 'info'
})

onMounted(async () => { try { active.value = await activeModel() } catch { /* ignore */ } })
defineExpose({ active, refresh: async () => { active.value = await activeModel() } })
</script>
