<template>
  <div class="table-scroll result-table-shell">
    <el-table :data="results" size="small" empty-text="暂无检测目标" class="result-table">
      <el-table-column label="类别" min-width="160">
        <template #default="{ row }">
          <div class="class-pair">
            <strong>{{ row.class_zh || row.class }}</strong>
            <span>{{ row.class }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="confidence" label="置信度" width="170">
        <template #default="{ row }">
          <div class="confidence-cell">
            <el-progress :percentage="Math.round(row.confidence * 100)" :stroke-width="8" :show-text="false" />
            <span>{{ (row.confidence * 100).toFixed(1) }}%</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="检测框坐标" min-width="220">
        <template #default="{ row }">[{{ row.bbox.map((v: number) => v.toFixed(1)).join(', ') }}]</template>
      </el-table-column>
      <el-table-column prop="frame_id" label="帧号" width="100" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { DetectionResult } from '@/api/types'

defineProps<{ results: DetectionResult[] }>()
</script>
