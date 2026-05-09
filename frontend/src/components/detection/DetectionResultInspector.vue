<template>
  <el-card shadow="never">
    <template #header>
      <div class="flex-between">
        <span style="font-weight:700;">检测结果</span>
        <el-tag v-if="resultCount > 0" type="primary" size="small">{{ resultCount }} 个目标</el-tag>
        <el-tag v-else type="info" size="small">无目标</el-tag>
      </div>
    </template>

    <!-- 摘要统计 -->
    <div class="result-inspector-stats">
      <div class="stat-item">
        <span class="stat-label">目标总数</span>
        <span class="stat-value">{{ resultCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">类别数</span>
        <span class="stat-value">{{ classCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均置信度</span>
        <span class="stat-value">{{ avgConfidence }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">耗时</span>
        <span class="stat-value">{{ duration }}ms</span>
      </div>
    </div>

    <!-- 类别标签 -->
    <div v-if="classSummary.length" class="flex-wrap" style="margin-bottom:10px;">
      <el-tag v-for="item in classSummary" :key="item.class" size="small" type="success" class="tag">
        {{ item.class_zh || item.class }} ×{{ item.count }}
      </el-tag>
    </div>

    <!-- 结果表 -->
    <DetectionResultTable :results="results" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DetectionResult } from '@/api/types'
import DetectionResultTable from './DetectionResultTable.vue'

const props = withDefaults(defineProps<{
  results: DetectionResult[]
  duration?: number
}>(), {
  duration: 0,
})

const resultCount = computed(() => props.results.length)
const classCount = computed(() => new Set(props.results.map((r) => r.class)).size)
const avgConfidence = computed(() => {
  if (!props.results.length) return 0
  const avg = props.results.reduce((sum, r) => sum + r.confidence, 0) / props.results.length
  return (avg * 100).toFixed(1)
})
const duration = computed(() => props.duration)
const classSummary = computed(() => {
  const map = new Map<string, { class: string; class_zh: string; count: number }>()
  for (const r of props.results) {
    const existing = map.get(r.class)
    if (existing) { existing.count++ } else { map.set(r.class, { class: r.class, class_zh: r.class_zh || '', count: 1 }) }
  }
  return Array.from(map.values()).sort((a, b) => b.count - a.count)
})
</script>
