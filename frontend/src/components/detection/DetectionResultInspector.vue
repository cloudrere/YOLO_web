<template>
  <div>
    <div class="grid four" style="margin-bottom:var(--gap);">
      <div class="metric-card"><span class="metric-label">目标总数</span><span class="metric-value">{{ total }}</span></div>
      <div class="metric-card"><span class="metric-label">类别数</span><span class="metric-value">{{ classCount }}</span></div>
      <div class="metric-card"><span class="metric-label">平均置信度</span><span class="metric-value">{{ avgConf }}%</span></div>
      <div class="metric-card"><span class="metric-label">耗时</span><span class="metric-value">{{ duration }}ms</span></div>
    </div>
    <div v-if="classTags.length" class="flex-wrap" style="margin-bottom:12px;">
      <el-tag v-for="c in classTags" :key="c.name" size="small" type="success">{{ c.name }} {{ c.count }}</el-tag>
    </div>
    <slot name="table" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface ResultItem { class: string; class_zh?: string; confidence: number }

const props = defineProps<{ results: ResultItem[]; duration?: number }>()

const total = computed(() => props.results.length)
const classCount = computed(() => new Set(props.results.map(r => r.class)).size)
const avgConf = computed(() => {
  if (!props.results.length) return 0
  return Math.round(props.results.reduce((s, r) => s + r.confidence, 0) / props.results.length * 100)
})
const duration = computed(() => props.duration || 0)
const classTags = computed(() => {
  const map = new Map<string, number>()
  props.results.forEach(r => { map.set(r.class_zh || r.class, (map.get(r.class_zh || r.class) || 0) + 1) })
  return Array.from(map.entries()).map(([name, count]) => ({ name, count }))
})
</script>
