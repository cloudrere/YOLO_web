<template>
  <el-card shadow="never">
    <template #header><span style="font-weight:700;">检测参数</span></template>
    <div class="param-group">
      <label class="param-label">置信度阈值 (Confidence)</label>
      <el-slider v-model="local.confidence" :min="0.1" :max="0.9" :step="0.05" :format-tooltip="(v: number) => v.toFixed(2)" show-input />
    </div>
    <div class="param-group">
      <label class="param-label">IoU 阈值</label>
      <el-slider v-model="local.iou" :min="0.1" :max="0.9" :step="0.05" :format-tooltip="(v: number) => v.toFixed(2)" show-input />
    </div>
    <div class="param-group">
      <el-checkbox v-model="local.save_history">保存检测记录</el-checkbox>
    </div>
    <slot name="extra-params" />
    <div style="margin-top:14px;">
      <el-button type="primary" class="full" :loading="running" :disabled="!canRun" @click="$emit('run')">
        {{ runLabel }}
      </el-button>
    </div>
    <div v-if="$slots.notes" class="text-muted" style="margin-top:10px;">
      <slot name="notes" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

const props = withDefaults(defineProps<{
  confidence?: number
  iou?: number
  saveHistory?: boolean
  running?: boolean
  canRun?: boolean
  runLabel?: string
}>(), {
  confidence: 0.5,
  iou: 0.45,
  saveHistory: true,
  running: false,
  canRun: true,
  runLabel: '开始检测',
})

defineEmits<{ run: [] }>()

const local = reactive({ confidence: props.confidence, iou: props.iou, save_history: props.saveHistory })

watch(() => props.confidence, (v) => { local.confidence = v })
watch(() => props.iou, (v) => { local.iou = v })
watch(() => props.saveHistory, (v) => { local.save_history = v })

defineExpose({ getParams: () => ({ confidence: local.confidence, iou: local.iou, save_history: local.save_history }) })
</script>

<style scoped>
.param-group { margin-bottom: 12px; }
.param-label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: var(--color-ink); }
</style>
