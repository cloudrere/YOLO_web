<template>
  <el-table :data="results" size="small" empty-text="No detections">
    <el-table-column prop="class" label="Class" />
    <el-table-column prop="confidence" label="Confidence" width="130">
      <template #default="{ row }">{{ row.confidence.toFixed(4) }}</template>
    </el-table-column>
    <el-table-column label="BBox">
      <template #default="{ row }">[{{ row.bbox.map((v: number) => v.toFixed(1)).join(', ') }}]</template>
    </el-table-column>
    <el-table-column prop="frame_id" label="Frame" width="100" />
  </el-table>
</template>

<script setup lang="ts">
import type { DetectionResult } from '@/api/types'

defineProps<{ results: DetectionResult[] }>()
</script>
