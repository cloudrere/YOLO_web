<template>
  <AppLayout>
    <!-- Hero 横幅：当前激活模型 + 4 状态胶囊 -->
    <div class="workstation-hero">
      <div style="flex:1;min-width:0;">
        <span class="eyebrow dark">模型控制室</span>
        <h2>{{ active?.active_model?.display_name || active?.active_model?.name || '尚未激活模型' }}</h2>
        <p style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ active?.model_path || '请先上传或登记模型，然后选择推理设备并激活。' }}</p>
      </div>
      <div class="model-command-stats" style="display:grid;grid-template-columns:repeat(4,auto);gap:12px;flex-shrink:0;">
        <div class="metric-card" style="padding:10px 16px;">
          <span class="metric-label">当前选择</span>
          <span class="metric-value" style="font-size:20px;">{{ deviceLabel(active?.requested_device || 'auto') }}</span>
        </div>
        <div class="metric-card" style="padding:10px 16px;">
          <span class="metric-label">实际运行</span>
          <span class="metric-value" style="font-size:20px;">{{ active?.device || '-' }}</span>
        </div>
        <div class="metric-card" style="padding:10px 16px;">
          <span class="metric-label">预热状态</span>
          <span
            class="metric-value"
            style="font-size:20px;"
            :style="{
              color:
                active?.warmup_status === 'cuda_ready' || active?.warmup_status === 'cpu_ready'
                  ? 'var(--status-success)'
                  : active?.warmup_status === 'failed'
                    ? 'var(--status-danger)'
                    : 'var(--status-warning)',
            }"
          >{{ warmupText }}</span>
        </div>
        <div class="metric-card" style="padding:10px 16px;">
          <span class="metric-label">CUDA</span>
          <span
            class="metric-value"
            style="font-size:20px;"
            :style="{ color: active?.cuda_available ? 'var(--status-success)' : 'var(--color-soft)' }"
          >{{ active?.cuda_available ? active.cuda_name || '可用' : '不可用' }}</span>
        </div>
      </div>
    </div>

    <!-- 双栏：设备切换 + 模型导入 -->
    <section class="grid two" style="margin-bottom:var(--gap);">
      <!-- 左栏：推理设备切换 -->
      <el-card shadow="never" class="panel-card device-control-panel">
        <template #header>
          <span style="font-weight:700;font-size:15px;">推理设备切换</span>
        </template>
        <div class="device-switcher flex-wrap" style="gap:8px;margin-bottom:14px;">
          <el-button
            v-for="option in displayDeviceOptions"
            :key="option.value"
            :type="selectedDevice === option.value ? 'primary' : 'default'"
            :disabled="!option.available || switchingDevice || !canManageModel"
            @click="selectedDevice = option.value"
            size="large"
          >
            {{ option.label }}
          </el-button>
        </div>
        <div
          class="device-detail-card"
          :class="selectedDevice.startsWith('cuda') ? 'gpu' : selectedDevice === 'cpu' ? 'cpu' : 'auto'"
          style="padding:16px;border-radius:var(--radius-md);margin-bottom:14px;"
          :style="{
            background: selectedDevice.startsWith('cuda') ? 'rgba(22,163,74,0.06)' : selectedDevice === 'cpu' ? 'rgba(217,119,6,0.06)' : 'rgba(37,99,235,0.05)',
            border: selectedDevice.startsWith('cuda') ? '1px solid rgba(22,163,74,0.2)' : selectedDevice === 'cpu' ? '1px solid rgba(217,119,6,0.2)' : '1px solid rgba(37,99,235,0.15)',
          }"
        >
          <strong style="display:block;font-size:16px;color:var(--color-ink);margin-bottom:4px;">{{ deviceLabel(selectedDevice) }}</strong>
          <span style="display:block;font-size:13px;color:var(--color-muted);margin-bottom:4px;">{{ selectedDeviceDescription }}</span>
          <small v-if="selectedDeviceDetail" style="color:var(--color-soft);font-size:12px;">{{ selectedDeviceDetail }}</small>
        </div>
        <el-button class="full" type="primary" size="large" :loading="switchingDevice" :disabled="!active?.active_model || !canManageModel" @click="switchDevice">
          切换并预热
        </el-button>
        <p v-if="active?.warmup_error" class="error-text" style="margin:12px 0 0;">{{ active.warmup_error }}</p>
      </el-card>

      <!-- 右栏：导入模型 -->
      <el-card shadow="never" class="panel-card model-register-card compact-form-card">
        <template #header>
          <span style="font-weight:700;font-size:15px;">导入模型</span>
        </template>
        <el-form :model="form" label-position="top" style="margin-bottom:16px;">
          <el-form-item label="模型名称" required>
            <el-input v-model="form.name" placeholder="输入模型显示名称" />
          </el-form-item>
          <el-form-item label="模型路径" required>
            <el-input v-model="form.path" placeholder="绝对路径或 storage/models 下的文件名" />
          </el-form-item>
          <el-form-item label="版本号" required>
            <el-input v-model="form.version" placeholder="输入版本标识" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!canManageModel || !canRegisterModel" @click="register" style="width:100%;">
              登记路径
            </el-button>
          </el-form-item>
        </el-form>
        <div class="model-upload-zone" style="padding:16px;border-radius:var(--radius-md);background:var(--color-bg);border:1px dashed var(--color-border);">
          <p style="margin:0 0 12px;font-size:13px;color:var(--color-muted);">上传 .pt 模型文件</p>
          <div class="flex-wrap" style="gap:8px;">
            <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel">
              <el-button>选择 .pt 文件</el-button>
            </el-upload>
            <el-button type="primary" :disabled="!uploadFileRef || !canManageModel" @click="upload">上传模型</el-button>
          </div>
        </div>
      </el-card>
    </section>

    <!-- 模型库表格 -->
    <el-card shadow="never" class="panel-card model-library-panel">
      <template #header>
        <div class="flex-between">
          <span style="font-weight:700;font-size:15px;">模型库</span>
          <el-button @click="load" :icon="'Refresh'">刷新</el-button>
        </div>
      </template>
      <div class="table-scroll model-table-shell">
        <el-table :data="models" class="model-table" empty-text="暂无已登记模型">
          <el-table-column label="#" width="60" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="display_name" label="显示名称" min-width="150">
            <template #default="{ row }">
              <span style="font-weight:600;">{{ row.display_name || row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="后端名称" min-width="140" />
          <el-table-column prop="version" label="版本" width="110">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.version }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="device" label="上次选择" width="120">
            <template #default="{ row }">
              <el-tag
                :type="row.device?.startsWith('cuda') ? 'success' : row.device === 'cpu' ? 'warning' : 'info'"
                size="small"
              >
                {{ deviceLabel(row.device || 'auto') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="激活状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '运行中' : '未激活' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="path" label="模型路径" min-width="260">
            <template #default="{ row }">
              <el-tooltip :content="row.path" placement="top">
                <span style="font-size:12px;font-family:var(--font-mono);color:var(--color-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;max-width:280px;">{{ row.path }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="360" fixed="right">
            <template #default="{ row }">
              <div class="flex-wrap" style="gap:6px;">
                <template v-if="canManageModel">
                  <el-button type="primary" size="small" :loading="activatingId === row.id" @click="activate(row.id)">激活</el-button>
                  <el-button size="small" @click="openDisplayName(row)">改名</el-button>
                  <el-button size="small" @click="openMapping(row)">类别映射</el-button>
                  <el-button type="danger" size="small" :disabled="row.is_active" @click="remove(row.id)">删除</el-button>
                </template>
                <el-tag v-else type="info" size="small">仅查看</el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 修改显示名称对话框 -->
    <el-dialog v-model="displayDialog" title="修改模型显示名称" width="420px">
      <el-input v-model="displayNameForm" placeholder="请输入前端显示名称" size="large" />
      <template #footer>
        <el-button @click="displayDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDisplayName">保存</el-button>
      </template>
    </el-dialog>

    <!-- 类别映射抽屉 -->
    <el-drawer v-model="mappingDrawer" title="类别中英文对照" size="54%">
      <div class="mapping-toolbar flex-between" style="margin-bottom:16px;">
        <span style="font-weight:600;color:var(--color-ink);">模型：{{ selectedModel?.display_name || selectedModel?.name }}</span>
        <el-button type="primary" @click="saveMapping">保存映射</el-button>
      </div>
      <div class="table-scroll">
        <el-table :data="mappingRows" empty-text="暂无类别数据">
          <el-table-column prop="class_name" label="英文类别" min-width="160" />
          <el-table-column label="中文名称" min-width="220">
            <template #default="{ row }">
              <el-input v-model="row.class_zh" placeholder="输入中文名称" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import {
  activateModel,
  activeModel,
  deleteModel,
  listModels,
  registerModel,
  switchModelDevice,
  updateModelClassMapping,
  updateModelDisplayName,
  uploadModel,
} from '@/api/model'
import { useAuthStore } from '@/stores/auth'
import type { ModelDeviceInfo, ModelEngineState, ModelInfo } from '@/api/types'

const auth = useAuthStore()
const models = ref<ModelInfo[]>([])
const active = ref<ModelEngineState | null>(null)
const uploadFileRef = ref<File | null>(null)
const activatingId = ref<number | null>(null)
const switchingDevice = ref(false)
const selectedDevice = ref('auto')
const form = reactive({ name: '', path: '', version: '' })
const displayDialog = ref(false)
const displayNameForm = ref('')
const mappingDrawer = ref(false)
const selectedModel = ref<ModelInfo | null>(null)
const mappingRows = ref<Array<{ class_name: string; class_zh: string }>>([])

const canManageModel = computed(() => auth.hasPermission('model:manage'))
const canRegisterModel = computed(() => Boolean(form.name.trim() && form.path.trim() && form.version.trim()))
const displayDeviceOptions = computed<ModelDeviceInfo[]>(() => {
  const options = active.value?.available_devices || [{ value: 'auto', label: '自动', type: 'auto', available: true }, { value: 'cpu', label: 'CPU', type: 'cpu', available: true }]
  return options.map((option) => ({ ...option, label: deviceLabel(option.value) }))
})
const warmupText = computed(() => {
  const status = active.value?.warmup_status || 'idle'
  return {
    cuda_ready: 'GPU 就绪',
    cpu_ready: 'CPU 就绪',
    pending: '等待初始化',
    failed: '初始化失败',
    not_loaded: '未加载',
    idle: '未初始化',
  }[status] || status
})
const selectedDeviceDetail = computed(() => {
  const option = active.value?.available_devices.find((item) => item.value === selectedDevice.value)
  if (!option) return ''
  if (selectedDevice.value.startsWith('cuda')) return `GPU 型号：${option.label || active.value?.cuda_name || selectedDevice.value}`
  return option.label && option.label !== deviceLabel(option.value) ? option.label : ''
})
const selectedDeviceDescription = computed(() => {
  if (selectedDevice.value === 'auto') return '系统自动优先使用可用 GPU，不可用时使用 CPU。'
  if (selectedDevice.value === 'cpu') return '强制使用 CPU，适合调试或显存不足时运行。'
  return '强制使用指定 GPU，CUDA 不可用时会直接返回错误。'
})

function deviceLabel(value: string) {
  if (!value || value === 'auto') return '自动'
  if (value === 'cpu') return 'CPU'
  if (value.startsWith('cuda')) return 'GPU'
  return value
}
function selectUploadModel(file: UploadFile) {
  uploadFileRef.value = file.raw || null
}
async function load() {
  models.value = (await listModels()).items
  active.value = await activeModel()
  selectedDevice.value = active.value.requested_device || 'auto'
}
async function register() {
  const name = form.name.trim()
  const path = form.path.trim()
  const version = form.version.trim()
  if (!name || !path || !version) {
    ElMessage.warning('模型名称、路径和版本号不能为空')
    return
  }
  await registerModel({ name, path, version, class_names: [] })
  Object.assign(form, { name: '', path: '', version: '' })
  ElMessage.success('模型路径已登记')
  await load()
}
async function upload() {
  if (!uploadFileRef.value) return
  await uploadModel(uploadFileRef.value)
  uploadFileRef.value = null
  ElMessage.success('模型文件已上传')
  await load()
}
async function switchDevice() {
  switchingDevice.value = true
  try {
    active.value = await switchModelDevice(selectedDevice.value)
    models.value = (await listModels()).items
    ElMessage.success('推理设备已切换并预热')
  } finally {
    switchingDevice.value = false
  }
}
async function activate(id: number) {
  activatingId.value = id
  try {
    await activateModel(id, selectedDevice.value)
    ElMessage.success('模型已激活')
    await load()
  } finally {
    activatingId.value = null
  }
}
function openDisplayName(row: ModelInfo) {
  selectedModel.value = row
  displayNameForm.value = row.display_name || row.name
  displayDialog.value = true
}
async function saveDisplayName() {
  if (!selectedModel.value) return
  await updateModelDisplayName(selectedModel.value.id, displayNameForm.value)
  displayDialog.value = false
  ElMessage.success('模型显示名称已更新')
  await load()
}
function openMapping(row: ModelInfo) {
  selectedModel.value = row
  const classNames = parseJson<string[]>(row.class_names_json, [])
  const mapping = parseJson<Record<string, string>>(row.class_mapping_json, {})
  mappingRows.value = classNames.map((className) => ({ class_name: className, class_zh: mapping[className] || className }))
  mappingDrawer.value = true
}
async function saveMapping() {
  if (!selectedModel.value) return
  const mapping = Object.fromEntries(mappingRows.value.map((row) => [row.class_name, row.class_zh]))
  await updateModelClassMapping(selectedModel.value.id, mapping)
  mappingDrawer.value = false
  ElMessage.success('类别映射已保存')
  await load()
}
async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这个未激活模型吗？模型记录删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteModel(id)
  ElMessage.success('模型已删除')
  await load()
}
function parseJson<T>(text: string, fallback: T): T {
  try {
    return JSON.parse(text) as T
  } catch {
    return fallback
  }
}
onMounted(load)
</script>
