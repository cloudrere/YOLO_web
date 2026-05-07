<template>
  <el-card class="analysis-card" shadow="never">
    <template #header>AI Analysis</template>
    <p>{{ analysis.summary }}</p>
    <el-table :data="analysis.class_distribution" size="small" empty-text="No classes">
      <el-table-column prop="class" label="Class" />
      <el-table-column prop="count" label="Count" width="90" />
      <el-table-column prop="avg_confidence" label="Avg Confidence" width="150" />
      <el-table-column prop="ratio" label="Ratio" width="100" />
    </el-table>
    <div class="tips">
      <el-tag v-for="tip in analysis.anomaly_tips" :key="tip" type="warning">{{ tip }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { AIAnalysis } from '@/api/types'

defineProps<{ analysis: AIAnalysis }>()
</script>
