<template>
  <div class="health-card-grid">
    <el-card shadow="never">
      <template #header><span style="font-weight:700;">GPU 状态</span></template>
      <div v-if="status?.gpu">
        <div class="health-status-line"><span>CUDA</span><el-tag :type="status.gpu.cuda_available ? 'success' : 'danger'" size="small">{{ status.gpu.cuda_available ? '可用' : '不可用' }}</el-tag></div>
        <div class="health-status-line"><span>GPU</span><strong>{{ status.gpu.gpu_name || '无' }}</strong></div>
        <div class="health-status-line"><span>显存</span><strong>{{ formatBytes(status.gpu.memory_total) }}</strong></div>
        <div class="health-status-line"><span>torch</span><strong>{{ status.gpu.torch_version || '-' }}</strong></div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight:700;">模型状态</span></template>
      <div v-if="status?.model">
        <div class="health-status-line"><span>激活模型</span><strong>{{ status.model.active_model_name || '无' }}</strong></div>
        <div class="health-status-line"><span>文件完整性</span><el-tag :type="status.model.active_model_exists ? 'success' : 'danger'" size="small">{{ status.model.active_model_exists ? '存在' : '缺失' }}</el-tag></div>
        <div class="health-status-line"><span>模型总数</span><strong>{{ status.model.total_models }}</strong></div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight:700;">数据库</span></template>
      <div v-if="status?.database">
        <div class="health-status-line"><span>连接</span><el-tag :type="status.database.connected ? 'success' : 'danger'" size="small">{{ status.database.connected ? '已连接' : '异常' }}</el-tag></div>
        <div class="health-status-line"><span>表完整性</span><el-tag :type="status.database.tables_ok ? 'success' : 'danger'" size="small">{{ status.database.tables_ok ? '完整' : '异常' }}</el-tag></div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight:700;">文件系统</span></template>
      <div v-if="status?.filesystem?.disk">
        <div class="health-status-line"><span>磁盘剩余</span><strong>{{ formatBytes(status.filesystem.disk.free) }}</strong></div>
        <div class="health-status-line"><span>磁盘总量</span><strong>{{ formatBytes(status.filesystem.disk.total) }}</strong></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import type { MaintenanceStatus } from '@/api/maintenance'

defineProps<{ status: MaintenanceStatus | null }>()

function formatBytes(value?: number) {
  const size = Number(value || 0)
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1)
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}
</script>
