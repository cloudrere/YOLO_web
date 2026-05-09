<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>运行环境体检</h2>
        <p>检查 GPU 算力、模型完整性、数据库连接与文件系统状况，评估系统是否处于生产可用状态。</p>
      </div>
      <el-button :loading="loading" @click="loadStatus">刷新体检</el-button>
    </section>

    <!-- 四卡体检面板 -->
    <SystemHealthCard :status="status" style="margin-bottom:var(--gap);" />

    <!-- GPU 诊断详情 -->
    <el-card v-if="status?.gpu.diagnostics?.length" shadow="never" style="margin-bottom:var(--gap);">
      <template #header><span style="font-weight:700;">GPU 诊断详情</span></template>
      <div style="display:grid;gap:6px;">
        <div v-for="item in status.gpu.diagnostics" :key="`${item.name}-${item.message}`" style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;background:var(--color-bg);">
          <el-tag :type="tagType(item.status)" size="small">{{ item.name }}</el-tag>
          <span style="font-size:13px;">{{ item.message }}</span>
        </div>
      </div>
    </el-card>

    <!-- 路径清单 -->
    <el-card v-if="status?.filesystem?.paths" shadow="never" style="margin-bottom:var(--gap);">
      <template #header><span style="font-weight:700;">存储路径清单</span></template>
      <div style="display:grid;gap:6px;">
        <div v-for="(item, name) in status.filesystem.paths" :key="name" style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;background:var(--color-bg);">
          <el-tag :type="item.exists && item.is_dir ? 'success' : 'danger'" size="small">{{ name }}</el-tag>
          <code style="font-size:12px;color:var(--color-muted);">{{ item.path }}</code>
        </div>
      </div>
    </el-card>

    <!-- 危险操作区 -->
    <el-card shadow="never" class="danger-zone">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-weight:700;color:#991b1b;">维护操作（危险区）</span>
          <el-tag type="danger" size="small">需二次确认</el-tag>
        </div>
      </template>
      <p style="margin:0 0 16px;font-size:13px;color:var(--color-muted);">以下操作会不可逆地清除数据，请在执行前确认影响范围。</p>
      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;">
        <div v-for="item in actions" :key="item.key" style="display:flex;align-items:center;justify-content:space-between;padding:16px;border-radius:var(--radius-md);background:var(--color-bg);border:1px solid var(--color-border);">
          <div>
            <strong style="display:block;font-size:14px;">{{ item.title }}</strong>
            <span style="display:block;font-size:12px;color:var(--color-muted);margin-top:4px;">{{ item.desc }}</span>
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
import SystemHealthCard from '@/components/shared/SystemHealthCard.vue'
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
</script>
