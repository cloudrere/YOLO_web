<template>
  <el-card class="analysis-card" shadow="never">
    <template #header>智能统计分析</template>
    <p>{{ analysis.summary }}</p>
    <el-table :data="analysis.class_distribution" size="small" empty-text="暂无类别分布">
      <el-table-column label="类别" min-width="150">
        <template #default="{ row }">
          <div class="class-pair">
            <strong>{{ row.class_zh || row.class }}</strong>
            <span>{{ row.class }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="count" label="数量" width="90" />
      <el-table-column prop="avg_confidence" label="平均置信度" width="150" />
      <el-table-column prop="ratio" label="占比" width="100" />
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
