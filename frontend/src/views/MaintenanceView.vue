<template>
  <AppLayout>
    <section class="maintenance-hero panel-card">
      <div>
        <span class="eyebrow dark">System Maintenance</span>
        <h2>系统维护</h2>
        <p>集中检查 GPU、模型、数据库和文件系统状态，并执行高风险清理操作。</p>
      </div>
      <div class="form-actions">
        <el-button :loading="loading" @click="loadStatus">刷新状态</el-button>
      </div>
    </section>

    <section class="grid two maintenance-status-grid stagger-container">
      <MotionPanel effect="glow" style="animation-delay:0ms">
        <el-card shadow="never" class="panel-card maintenance-status-card">
          <template #header><div class="card-header-row"><span>GPU 状态</span><StatusPulse :status="status?.gpu?.cuda_available ? 'success' : 'danger'" size="sm" /></div></template>
          <div class="status-line"><span>CUDA</span><el-tag :type="status?.gpu.cuda_available ? 'success' : 'danger'">{{ status?.gpu.cuda_available ? '可用' : '不可用' }}</el-tag></div>
          <div class="status-line"><span>torch</span><strong>{{ status?.gpu.torch_version || '未检测到' }}</strong></div>
          <div class="status-line"><span>CUDA 运行时</span><strong>{{ status?.gpu.torch_cuda_version || '未检测到' }}</strong></div>
          <div class="status-line"><span>GPU 名称</span><strong>{{ status?.gpu.gpu_name || '暂无' }}</strong></div>
          <div class="status-line"><span>显存</span><strong>{{ formatBytes(status?.gpu.memory_total) }}</strong></div>
          <div class="diagnostic-list">
            <div v-for="item in status?.gpu.diagnostics || []" :key="`${item.name}-${item.message}`">
              <el-tag :type="tagType(item.status)">{{ item.name }}</el-tag>
              <span>{{ item.message }}</span>
            </div>
          </div>
        </el-card>
      </MotionPanel>

      <MotionPanel effect="glow" style="animation-delay:100ms">
        <el-card shadow="never" class="panel-card maintenance-status-card">
          <template #header><div class="card-header-row"><span>模型状态</span><StatusPulse :status="status?.model?.active_model_exists ? 'success' : 'danger'" size="sm" /></div></template>
          <div class="status-line"><span>当前激活模型</span><strong>{{ status?.model.active_model_name || '暂无' }}</strong></div>
          <div class="status-line"><span>文件完整性</span><el-tag :type="status?.model.active_model_exists ? 'success' : 'danger'">{{ status?.model.active_model_exists ? '文件存在' : '文件缺失' }}</el-tag></div>
          <div class="status-line"><span>模型数量</span><strong>{{ status?.model.total_models ?? 0 }}</strong></div>
          <div class="path-box">{{ status?.model.active_model_path || '暂无模型路径' }}</div>
        </el-card>
      </MotionPanel>

      <MotionPanel effect="glow" style="animation-delay:200ms">
        <el-card shadow="never" class="panel-card maintenance-status-card">
          <template #header><div class="card-header-row"><span>数据库状态</span><StatusPulse :status="status?.database?.connected ? 'success' : 'danger'" size="sm" /></div></template>
          <div class="status-line"><span>连接状态</span><el-tag :type="status?.database.connected ? 'success' : 'danger'">{{ status?.database.connected ? '已连接' : '异常' }}</el-tag></div>
          <div class="status-line"><span>表完整性</span><el-tag :type="status?.database.tables_ok ? 'success' : 'danger'">{{ status?.database.tables_ok ? '完整' : '缺失' }}</el-tag></div>
          <div class="status-line"><span>表数量</span><strong>{{ status?.database.table_count ?? 0 }}</strong></div>
          <div class="path-box">{{ status?.database.missing_tables?.length ? `缺失表：${status.database.missing_tables.join(', ')}` : '关键表结构正常' }}</div>
        </el-card>
      </MotionPanel>

      <MotionPanel effect="glow" style="animation-delay:300ms">
        <el-card shadow="never" class="panel-card maintenance-status-card">
          <template #header><div class="card-header-row"><span>文件系统</span><StatusPulse :status="Object.values(status?.filesystem?.paths || {}).every((p: any) => p.exists) ? 'success' : 'warning'" size="sm" /></div></template>
          <div class="status-line"><span>磁盘剩余</span><strong>{{ formatBytes(status?.filesystem.disk.free) }}</strong></div>
          <div class="status-line"><span>磁盘总量</span><strong>{{ formatBytes(status?.filesystem.disk.total) }}</strong></div>
          <div class="maintenance-paths">
            <div v-for="(item, name) in status?.filesystem.paths || {}" :key="name">
              <el-tag :type="item.exists && item.is_dir ? 'success' : 'danger'">{{ name }}</el-tag>
              <span>{{ item.path }}</span>
            </div>
          </div>
        </el-card>
      </MotionPanel>
    </section>

    <el-card shadow="never" class="panel-card maintenance-actions-panel">
      <template #header>维护操作</template>
      <div class="maintenance-actions-grid">
        <div v-for="item in actions" :key="item.key" class="maintenance-action-card">
          <div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
          <el-button type="danger" :loading="runningAction === item.key" @click="runAction(item)">{{ item.button }}</el-button>
        </div>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'
import MotionPanel from '@/components/common/MotionPanel.vue'
import {
  clearMaintenanceHistory,
  clearMaintenanceLogs,
  clearMaintenanceModels,
  getMaintenanceStatus,
  restoreInitialState,
  type MaintenanceStatus,
} from '@/api/maintenance'

type MaintenanceAction = {
  key: string
  title: string
  desc: string
  button: string
  confirm: string
  run: () => Promise<unknown>
}

const status = ref<MaintenanceStatus | null>(null)
const loading = ref(false)
const runningAction = ref('')

const actions = computed<MaintenanceAction[]>(() => [
  {
    key: 'history',
    title: '清除检测历史',
    desc: '清空检测记录数据库、上传文件和检测结果文件，保留 storage 目录结构。',
    button: '清除历史',
    confirm: '确认清除全部检测历史吗？数据库记录和检测文件都会被清空。',
    run: clearMaintenanceHistory,
  },
  {
    key: 'logs',
    title: '清除日志',
    desc: '清空系统日志数据库和本地日志文件，保留日志目录结构。',
    button: '清除日志',
    confirm: '确认清除全部系统日志吗？日志数据库记录和日志文件都会被清空。',
    run: clearMaintenanceLogs,
  },
  {
    key: 'models',
    title: '清除模型',
    desc: '清除非激活模型记录和 storage/models 下的非激活模型文件，不影响当前激活模型。',
    button: '清除模型',
    confirm: '确认清除全部非激活模型吗？当前激活模型会保留。',
    run: clearMaintenanceModels,
  },
  {
    key: 'restore',
    title: '一键恢复初始化',
    desc: '恢复管理员账号、默认权限角色、系统基础字典和当前激活模型/默认模型。',
    button: '恢复初始化',
    confirm: '确认执行一键恢复初始化吗？系统会重新写入默认账号、权限、基础字典和默认模型状态。',
    run: restoreInitialState,
  },
])

onMounted(loadStatus)

async function loadStatus() {
  loading.value = true
  try {
    status.value = await getMaintenanceStatus()
  } finally {
    loading.value = false
  }
}
async function runAction(action: MaintenanceAction) {
  try {
    await ElMessageBox.confirm(action.confirm, action.title, { type: 'warning', confirmButtonText: '确认执行', cancelButtonText: '取消' })
  } catch {
    return
  }
  runningAction.value = action.key
  try {
    await action.run()
    ElMessage.success(`${action.title}已完成`)
    await loadStatus()
  } finally {
    runningAction.value = ''
  }
}
function tagType(status: string): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'ok') return 'success'
  if (status === 'error') return 'danger'
  if (status === 'warning') return 'warning'
  return 'info'
}
function formatBytes(value?: number) {
  const size = Number(value || 0)
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1)
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}
</script>

<style scoped>
/* 维护 Hero */
.maintenance-hero {
  background: linear-gradient(135deg, #fef2f2 0%, #fff7ed 50%, #fffbeb 100%);
  border: 1px solid #fecaca;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 状态卡片增强 */
.maintenance-status-card {
  position: relative;
  overflow: hidden;
}

.maintenance-status-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.maintenance-status-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 每张卡片不同颜色顶部条 */
:deep(.stagger-container > *:nth-child(1)) .maintenance-status-card::before {
  background: linear-gradient(90deg, #2563eb, #3b82f6);
}

:deep(.stagger-container > *:nth-child(2)) .maintenance-status-card::before {
  background: linear-gradient(90deg, #7c3aed, #8b5cf6);
}

:deep(.stagger-container > *:nth-child(3)) .maintenance-status-card::before {
  background: linear-gradient(90deg, #0891b2, #06b6d4);
}

:deep(.stagger-container > *:nth-child(4)) .maintenance-status-card::before {
  background: linear-gradient(90deg, #16a34a, #22c55e);
}

/* 维护操作卡片增强 */
.maintenance-action-card {
  transition: border-color var(--motion-fast), box-shadow var(--motion-fast);
}

.maintenance-action-card:hover {
  border-color: #fecaca;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.06);
}

.maintenance-action-card h3 {
  margin: 0 0 4px;
  font-size: 15px;
  color: var(--color-ink);
}

.maintenance-action-card p {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.6;
}

/* 路径框增强 */
.path-box {
  margin-top: 8px;
  background: #f1f5f9;
  border: 1px solid var(--color-border);
}

/* 诊断列表增强 */
.diagnostic-list {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
}

.diagnostic-list > div {
  padding: 4px 0;
}

@media (max-width: 768px) {
  .maintenance-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>