<template>
  <el-table :data="results" size="small" empty-text="暂无检测目标">
    <el-table-column prop="class" label="类别" />
    <el-table-column prop="confidence" label="置信度" width="130">
      <template #default="{ row }">{{ row.confidence.toFixed(4) }}</template>
    </el-table-column>
    <el-table-column label="检测框 bbox">
      <template #default="{ row }">[{{ row.bbox.map((v: number) => v.toFixed(1)).join(', ') }}]</template>
    </el-table-column>
    <el-table-column prop="frame_id" label="帧号" width="100" />
  </el-table>
</template>

<script setup lang="ts">
import type { DetectionResult } from '@/api/types'

defineProps<{ results: DetectionResult[] }>()
</script>
