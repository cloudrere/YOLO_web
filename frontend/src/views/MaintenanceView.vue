<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>系统维护</h1>
        <p>集中检查 GPU、模型、数据库和文件系统状态，并执行高风险清理操作。</p>
      </div>
      <el-button size="small" :loading="loading" @click="loadStatus">刷新状态</el-button>
    </div>

    <div class="ws-panel-2" style="grid-template-columns:repeat(2, 1fr)">
      <div class="ws-card">
        <div class="ws-card-header">GPU 状态</div>
        <div class="ws-card-body">
          <div class="ws-info-grid">
            <div class="ws-info-item">
              <span class="info-label">CUDA</span>
              <el-tag size="small" :type="status?.gpu.cuda_available ? 'success' : 'danger'">{{ status?.gpu.cuda_available ? '可用' : '不可用' }}</el-tag>
            </div>
            <div class="ws-info-item"><span class="info-label">torch</span><span class="info-value">{{ status?.gpu.torch_version || 'N/A' }}</span></div>
            <div class="ws-info-item"><span class="info-label">CUDA 运行时</span><span class="info-value">{{ status?.gpu.torch_cuda_version || 'N/A' }}</span></div>
            <div class="ws-info-item"><span class="info-label">GPU 名称</span><span class="info-value" style="font-size:10px">{{ status?.gpu.gpu_name || 'N/A' }}</span></div>
            <div class="ws-info-item"><span class="info-label">显存</span><span class="info-value">{{ formatBytes(status?.gpu.memory_total) }}</span></div>
          </div>
          <div class="ws-list" style="margin-top:8px">
            <div v-for="item in status?.gpu.diagnostics || []" :key="`${item.name}-${item.message}`" class="ws-list-item">
              <el-tag size="small" :type="tagType(item.status)">{{ item.name }}</el-tag>
              <span class="li-name">{{ item.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="ws-card">
        <div class="ws-card-header">模型状态</div>
        <div class="ws-card-body">
          <div class="ws-info-grid">
            <div class="ws-info-item"><span class="info-label">当前激活模型</span><span class="info-value" style="font-size:10px">{{ status?.model.active_model_name || 'N/A' }}</span></div>
            <div class="ws-info-item">
              <span class="info-label">文件完整性</span>
              <el-tag size="small" :type="status?.model.active_model_exists ? 'success' : 'danger'">{{ status?.model.active_model_exists ? '文件存在' : '文件缺失' }}</el-tag>
            </div>
            <div class="ws-info-item"><span class="info-label">模型数量</span><span class="info-value">{{ status?.model.total_models ?? 0 }}</span></div>
            <div class="ws-info-item"><span class="info-label">模型路径</span><span class="info-value" style="font-size:10px">{{ status?.model.active_model_path || 'N/A' }}</span></div>
          </div>
        </div>
      </div>

      <div class="ws-card">
        <div class="ws-card-header">数据库状态</div>
        <div class="ws-card-body">
          <div class="ws-info-grid">
            <div class="ws-info-item">
              <span class="info-label">连接状态</span>
              <el-tag size="small" :type="status?.database.connected ? 'success' : 'danger'">{{ status?.database.connected ? '已连接' : '异常' }}</el-tag>
            </div>
            <div class="ws-info-item">
              <span class="info-label">表完整性</span>
              <el-tag size="small" :type="status?.database.tables_ok ? 'success' : 'danger'">{{ status?.database.tables_ok ? '完整' : '缺失' }}</el-tag>
            </div>
            <div class="ws-info-item"><span class="info-label">表数量</span><span class="info-value">{{ status?.database.table_count ?? 0 }}</span></div>
            <div class="ws-info-item"><span class="info-label">缺失表</span><span class="info-value" style="font-size:10px">{{ status?.database.missing_tables?.length ? status.database.missing_tables.join(', ') : '关键表结构正常' }}</span></div>
          </div>
        </div>
      </div>

      <div class="ws-card">
        <div class="ws-card-header">文件系统</div>
        <div class="ws-card-body">
          <div class="ws-info-grid">
            <div class="ws-info-item"><span class="info-label">磁盘剩余</span><span class="info-value">{{ formatBytes(status?.filesystem.disk.free) }}</span></div>
            <div class="ws-info-item"><span class="info-label">磁盘总量</span><span class="info-value">{{ formatBytes(status?.filesystem.disk.total) }}</span></div>
          </div>
          <div class="ws-list" style="margin-top:8px">
            <div v-for="(item, name) in status?.filesystem.paths || {}" :key="name" class="ws-list-item">
              <el-tag size="small" :type="item.exists && item.is_dir ? 'success' : 'danger'">{{ String(name) }}</el-tag>
              <span class="li-name" style="font-family:var(--font-mono);font-size:10px">{{ item.path }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="ws-card" style="margin-top:12px">
      <div class="ws-card-header">维护操作</div>
      <div class="ws-card-body">
        <div class="ws-danger-zone">
          <div v-for="item in actions" :key="item.key" class="ws-danger-card">
            <h4>{{ item.title }}</h4>
            <p>{{ item.desc }}</p>
            <el-button type="danger" size="small" :loading="runningAction === item.key" @click="runAction(item)">{{ item.button }}</el-button>
          </div>
        </div>
      </div>
    </div>
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
  { key: 'models', title: '清除模型', desc: '清除非激活模型记录和文件，当前模型保留。', button: '清除模型', confirm: '确认清除全部非激活模型吗？', run: clearMaintenanceModels },
  { key: 'restore', title: '一键恢复初始化', desc: '恢复管理员、默认权限、基础字典和当前模型。', button: '恢复初始化', confirm: '确认执行一键恢复初始化吗？', run: restoreInitialState },
])

onMounted(loadStatus)

async function loadStatus() { loading.value = true; try { status.value = await getMaintenanceStatus() } finally { loading.value = false } }
async function runAction(action: MaintenanceAction) { try { await ElMessageBox.confirm(action.confirm, action.title, { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; runningAction.value = action.key; try { await action.run(); ElMessage.success(`${action.title}已完成`); await loadStatus() } finally { runningAction.value = '' } }
function tagType(status: string): 'success' | 'danger' | 'warning' | 'info' { if (status === 'ok') return 'success'; if (status === 'error') return 'danger'; if (status === 'warning') return 'warning'; return 'info' }
function formatBytes(value?: number) { const size = Number(value || 0); if (!size) return '0 B'; const units = ['B', 'KB', 'MB', 'GB', 'TB']; const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1); return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}` }
</script>
