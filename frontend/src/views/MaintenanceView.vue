<template>
  <AppLayout>
    <section class="maintenance-hero">
      <div>
        <span class="eyebrow dark">System Maintenance</span>
        <h2>系统维护</h2>
        <p>集中检查 GPU、模型、数据库和文件系统状态，并执行高风险清理操作。</p>
      </div>
      <el-button :loading="loading" @click="loadStatus">刷新状态</el-button>
    </section>

    <section class="grid two" style="margin-bottom: var(--gap);">
      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">GPU 状态</span></template>
        <div class="status-line"><span>CUDA</span><el-tag :type="status?.gpu.cuda_available ? 'success' : 'danger'" size="small">{{ status?.gpu.cuda_available ? '可用' : '不可用' }}</el-tag></div>
        <div class="status-line"><span>torch</span><strong>{{ status?.gpu.torch_version || '未检测到' }}</strong></div>
        <div class="status-line"><span>CUDA 运行时</span><strong>{{ status?.gpu.torch_cuda_version || '未检测到' }}</strong></div>
        <div class="status-line"><span>GPU 名称</span><strong>{{ status?.gpu.gpu_name || '暂无' }}</strong></div>
        <div class="status-line"><span>显存</span><strong>{{ formatBytes(status?.gpu.memory_total) }}</strong></div>
        <div class="diagnostic-list" style="margin-top: 12px;">
          <div v-for="item in status?.gpu.diagnostics || []" :key="`${item.name}-${item.message}`">
            <el-tag :type="tagType(item.status)" size="small">{{ item.name }}</el-tag>
            <span style="font-size: 13px;">{{ item.message }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">模型状态</span></template>
        <div class="status-line"><span>当前激活模型</span><strong>{{ status?.model.active_model_name || '暂无' }}</strong></div>
        <div class="status-line"><span>文件完整性</span><el-tag :type="status?.model.active_model_exists ? 'success' : 'danger'" size="small">{{ status?.model.active_model_exists ? '文件存在' : '文件缺失' }}</el-tag></div>
        <div class="status-line"><span>模型数量</span><strong>{{ status?.model.total_models ?? 0 }}</strong></div>
        <div class="path-box">{{ status?.model.active_model_path || '暂无模型路径' }}</div>
      </el-card>

      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">数据库状态</span></template>
        <div class="status-line"><span>连接状态</span><el-tag :type="status?.database.connected ? 'success' : 'danger'" size="small">{{ status?.database.connected ? '已连接' : '异常' }}</el-tag></div>
        <div class="status-line"><span>表完整性</span><el-tag :type="status?.database.tables_ok ? 'success' : 'danger'" size="small">{{ status?.database.tables_ok ? '完整' : '缺失' }}</el-tag></div>
        <div class="status-line"><span>表数量</span><strong>{{ status?.database.table_count ?? 0 }}</strong></div>
        <div class="path-box">{{ status?.database.missing_tables?.length ? `缺失表：${status.database.missing_tables.join(', ')}` : '关键表结构正常' }}</div>
      </el-card>

      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">文件系统</span></template>
        <div class="status-line"><span>磁盘剩余</span><strong>{{ formatBytes(status?.filesystem.disk.free) }}</strong></div>
        <div class="status-line"><span>磁盘总量</span><strong>{{ formatBytes(status?.filesystem.disk.total) }}</strong></div>
        <div class="maintenance-paths" style="margin-top: 10px;">
          <div v-for="(item, name) in status?.filesystem.paths || {}" :key="name">
            <el-tag :type="item.exists && item.is_dir ? 'success' : 'danger'" size="small">{{ name }}</el-tag>
            <span style="font-size: 13px;">{{ item.path }}</span>
          </div>
        </div>
      </el-card>
    </section>

    <el-card class="workstation-panel" shadow="never">
      <template #header><span style="font-weight: 700;">维护操作</span></template>
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
import { clearMaintenanceHistory, clearMaintenanceLogs, clearMaintenanceModels, getMaintenanceStatus, restoreInitialState, type MaintenanceStatus } from '@/api/maintenance'

type MaintenanceAction = { key: string; title: string; desc: string; button: string; confirm: string; run: () => Promise<unknown> }

const status = ref<MaintenanceStatus | null>(null)
const loading = ref(false)
const runningAction = ref('')

const actions = computed<MaintenanceAction[]>(() => [
  { key: 'history', title: '清除检测历史', desc: '清空检测记录数据库、上传文件和检测结果文件。', button: '清除历史', confirm: '确认清除全部检测历史吗？', run: clearMaintenanceHistory },
  { key: 'logs', title: '清除日志', desc: '清空系统日志数据库和本地日志文件。', button: '清除日志', confirm: '确认清除全部系统日志吗？', run: clearMaintenanceLogs },
  { key: 'models', title: '清除模型', desc: '清除非激活模型记录和文件。', button: '清除模型', confirm: '确认清除全部非激活模型吗？', run: clearMaintenanceModels },
  { key: 'restore', title: '一键恢复初始化', desc: '恢复管理员账号、默认权限角色和系统基础字典。', button: '恢复初始化', confirm: '确认执行一键恢复初始化吗？', run: restoreInitialState },
])

onMounted(loadStatus)

async function loadStatus() { loading.value = true; try { status.value = await getMaintenanceStatus() } finally { loading.value = false } }
async function runAction(action: MaintenanceAction) {
  try { await ElMessageBox.confirm(action.confirm, action.title, { type: 'warning', confirmButtonText: '确认执行', cancelButtonText: '取消' }) } catch { return }
  runningAction.value = action.key
  try { await action.run(); ElMessage.success(`${action.title}已完成`); await loadStatus() } finally { runningAction.value = '' }
}
function tagType(status: string): 'success' | 'danger' | 'warning' | 'info' { if (status === 'ok') return 'success'; if (status === 'error') return 'danger'; if (status === 'warning') return 'warning'; return 'info' }
function formatBytes(value?: number) { const size = Number(value || 0); if (!size) return '0 B'; const units = ['B', 'KB', 'MB', 'GB', 'TB']; const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1); return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}` }
</script>
