<template>
  <AppLayout>
    <!-- Hero: 当前激活模型突出显示 -->
    <section class="workstation-hero">
      <div>
        <h2>{{ active?.active_model?.display_name || active?.active_model?.name || '尚未激活模型' }}</h2>
        <p>{{ active?.model_path || '请先上传或登记模型，然后选择推理设备并激活。' }}</p>
      </div>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <div style="padding:8px 14px;border-radius:6px;background:#f8fafc;border:1px solid var(--color-border);text-align:center;">
          <span style="display:block;font-size:11px;color:var(--color-muted);">推理设备</span>
          <strong style="display:block;color:var(--color-ink);font-size:14px;">{{ deviceLabel(active?.requested_device || 'auto') }}</strong>
        </div>
        <div style="padding:8px 14px;border-radius:6px;background:#f8fafc;border:1px solid var(--color-border);text-align:center;">
          <span style="display:block;font-size:11px;color:var(--color-muted);">实际运行</span>
          <strong style="display:block;color:var(--color-ink);font-size:14px;">{{ active?.device || '-' }}</strong>
        </div>
        <div style="padding:8px 14px;border-radius:6px;background:#f8fafc;border:1px solid var(--color-border);text-align:center;">
          <span style="display:block;font-size:11px;color:var(--color-muted);">预热状态</span>
          <el-tag :type="warmupTagType" size="small">{{ warmupText }}</el-tag>
        </div>
        <div style="padding:8px 14px;border-radius:6px;background:#f8fafc;border:1px solid var(--color-border);text-align:center;">
          <span style="display:block;font-size:11px;color:var(--color-muted);">CUDA</span>
          <strong style="display:block;color:var(--color-ink);font-size:14px;">{{ active?.cuda_available ? active.cuda_name || '可用' : '不可用' }}</strong>
        </div>
      </div>
    </section>

    <!-- 设备切换 + 导入模型 -->
    <section class="grid two" style="margin-bottom:var(--gap);">
      <!-- 推理设备切换 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">推理设备切换</span></template>
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;">
          <el-button v-for="option in displayDeviceOptions" :key="option.value"
            :type="selectedDevice === option.value ? 'primary' : ''"
            :disabled="!option.available || switchingDevice || !canManageModel"
            size="small" @click="selectedDevice = option.value">
            {{ option.label }}
          </el-button>
        </div>
        <div style="margin:14px 0;padding:18px;border-radius:var(--radius-md);background:linear-gradient(135deg,#eff6ff,#f0f9ff);border:1px solid #bfdbfe;">
          <strong style="display:block;font-size:22px;color:var(--color-primary-deep);">{{ deviceLabel(selectedDevice) }}</strong>
          <span style="display:block;margin-top:8px;color:var(--color-muted);font-size:13px;">{{ selectedDeviceDescription }}</span>
          <small v-if="selectedDeviceDetail" style="display:block;margin-top:4px;color:var(--color-soft);">{{ selectedDeviceDetail }}</small>
        </div>
        <el-button class="full" type="primary" :loading="switchingDevice" :disabled="!active?.active_model || !canManageModel" @click="switchDevice">切换并预热</el-button>
        <p v-if="active?.warmup_error" class="error-text mt">{{ active.warmup_error }}</p>
      </el-card>

      <!-- 导入模型 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">导入模型</span></template>
        <el-form :model="form" label-position="top">
          <el-form-item label="模型名称" required><el-input v-model="form.name" placeholder="模型显示名称" /></el-form-item>
          <el-form-item label="模型路径" required><el-input v-model="form.path" placeholder="绝对路径或 storage/models 下文件名" /></el-form-item>
          <el-form-item label="版本号" required><el-input v-model="form.version" placeholder="版本标识" /></el-form-item>
          <el-button type="primary" :disabled="!canManageModel || !canRegisterModel" @click="register" style="width:100%;">登记路径</el-button>
        </el-form>
        <div style="display:flex;gap:10px;margin-top:14px;padding-top:14px;border-top:1px solid var(--color-border);">
          <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel" style="flex:1;"><el-button style="width:100%;">选择 .pt 文件</el-button></el-upload>
          <el-button type="primary" :disabled="!uploadFileRef" @click="upload">上传</el-button>
        </div>
      </el-card>
    </section>

    <!-- 模型库 -->
    <el-card shadow="never">
      <template #header>
        <div class="flex-between">
          <span style="font-weight:700;">模型库</span>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </template>
      <div class="table-scroll">
        <el-table :data="models" size="small">
          <el-table-column label="#" width="60"><template #default="{ $index }">{{ $index + 1 }}</template></el-table-column>
          <el-table-column prop="display_name" label="显示名称" min-width="150"><template #default="{ row }">{{ row.display_name || row.name }}</template></el-table-column>
          <el-table-column prop="name" label="后端名称" min-width="130" />
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column prop="device" label="设备" width="100">
            <template #default="{ row }"><el-tag :type="row.device?.startsWith('cuda') ? 'success' : row.device === 'cpu' ? 'warning' : 'info'" size="small">{{ deviceLabel(row.device || 'auto') }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="90">
            <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '运行中' : '未激活' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="path" label="路径" min-width="240" show-overflow-tooltip />
          <el-table-column label="操作" width="340" fixed="right">
            <template #default="{ row }">
              <div class="flex-wrap">
                <el-button v-if="canManageModel" type="primary" size="small" :loading="activatingId === row.id" @click="activate(row.id)">激活</el-button>
                <el-button v-if="canManageModel" size="small" @click="openDisplayName(row)">改名</el-button>
                <el-button v-if="canManageModel" size="small" @click="openMapping(row)">类别映射</el-button>
                <el-button v-if="canManageModel" type="danger" size="small" :disabled="row.is_active" @click="remove(row.id)">删除</el-button>
                <el-tag v-else type="info" size="small">仅查看</el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 对话框与抽屉保持不变 -->
    <el-dialog v-model="displayDialog" title="修改显示名称" width="420px">
      <el-input v-model="displayNameForm" placeholder="输入显示名称" />
      <template #footer><el-button @click="displayDialog = false">取消</el-button><el-button type="primary" @click="saveDisplayName">保存</el-button></template>
    </el-dialog>
    <el-drawer v-model="mappingDrawer" title="类别中英文对照" size="54%">
      <div class="flex-between" style="margin-bottom:16px;">
        <span>模型：{{ selectedModel?.display_name || selectedModel?.name }}</span>
        <el-button type="primary" size="small" @click="saveMapping">保存映射</el-button>
      </div>
      <div class="table-scroll">
        <el-table :data="mappingRows">
          <el-table-column prop="class_name" label="英文类别" min-width="160" />
          <el-table-column label="中文名称" min-width="220"><template #default="{ row }"><el-input v-model="row.class_zh" /></template></el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { activateModel, activeModel, deleteModel, listModels, registerModel, switchModelDevice, updateModelClassMapping, updateModelDisplayName, uploadModel } from '@/api/model'
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
  const map: Record<string, string> = { cuda_ready: 'GPU 就绪', cpu_ready: 'CPU 就绪', pending: '等待初始化', failed: '初始化失败', not_loaded: '未加载', idle: '未初始化' }
  return map[active.value?.warmup_status || ''] || active.value?.warmup_status || 'idle'
})
const warmupTagType = computed(() => {
  const s = active.value?.warmup_status || ''
  return s === 'cuda_ready' || s === 'cpu_ready' ? 'success' : s === 'failed' ? 'danger' : s === 'pending' ? 'warning' : 'info'
})
const selectedDeviceDetail = computed(() => {
  const option = active.value?.available_devices.find((item) => item.value === selectedDevice.value)
  if (!option) return ''
  if (selectedDevice.value.startsWith('cuda')) return `GPU 型号：${option.label || active.value?.cuda_name || selectedDevice.value}`
  return ''
})
const selectedDeviceDescription = computed(() => {
  if (selectedDevice.value === 'auto') return '系统自动优先使用可用 GPU，不可用时使用 CPU。'
  if (selectedDevice.value === 'cpu') return '强制使用 CPU，适合调试或显存不足时。'
  return '强制使用指定 GPU。'
})

function deviceLabel(value: string) { if (!value || value === 'auto') return '自动'; if (value === 'cpu') return 'CPU'; if (value.startsWith('cuda')) return 'GPU'; return value }
function selectUploadModel(file: UploadFile) { uploadFileRef.value = file.raw || null }
async function load() { models.value = (await listModels()).items; active.value = await activeModel(); selectedDevice.value = active.value.requested_device || 'auto' }
async function register() { const name = form.name.trim(); const path = form.path.trim(); const version = form.version.trim(); if (!name || !path || !version) { ElMessage.warning('名称、路径和版本不能为空'); return }; await registerModel({ name, path, version, class_names: [] }); Object.assign(form, { name: '', path: '', version: '' }); ElMessage.success('模型已登记'); await load() }
async function upload() { if (!uploadFileRef.value) return; await uploadModel(uploadFileRef.value); uploadFileRef.value = null; ElMessage.success('模型已上传'); await load() }
async function switchDevice() { switchingDevice.value = true; try { active.value = await switchModelDevice(selectedDevice.value); models.value = (await listModels()).items; ElMessage.success('设备已切换并预热') } finally { switchingDevice.value = false } }
async function activate(id: number) { activatingId.value = id; try { await activateModel(id, selectedDevice.value); ElMessage.success('模型已激活'); await load() } finally { activatingId.value = null } }
function openDisplayName(row: ModelInfo) { selectedModel.value = row; displayNameForm.value = row.display_name || row.name; displayDialog.value = true }
async function saveDisplayName() { if (!selectedModel.value) return; await updateModelDisplayName(selectedModel.value.id, displayNameForm.value); displayDialog.value = false; ElMessage.success('名称已更新'); await load() }
function openMapping(row: ModelInfo) { selectedModel.value = row; const classNames = parseJson<string[]>(row.class_names_json, []); const mapping = parseJson<Record<string, string>>(row.class_mapping_json, {}); mappingRows.value = classNames.map((className) => ({ class_name: className, class_zh: mapping[className] || className })); mappingDrawer.value = true }
async function saveMapping() { if (!selectedModel.value) return; const mapping = Object.fromEntries(mappingRows.value.map((row) => [row.class_name, row.class_zh])); await updateModelClassMapping(selectedModel.value.id, mapping); mappingDrawer.value = false; ElMessage.success('映射已保存'); await load() }
async function remove(id: number) { try { await ElMessageBox.confirm('确认删除这个未激活模型？', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteModel(id); ElMessage.success('模型已删除'); await load() }
function parseJson<T>(text: string, fallback: T): T { try { return JSON.parse(text) as T } catch { return fallback } }
onMounted(load)
</script>
