<template>
  <AppLayout>
    <div class="ws-card mb-s">
      <div class="ws-card-body">
        <div class="flex-between">
          <div>
            <h2 style="font-size:16px;margin-bottom:2px">{{ active?.active_model?.display_name || active?.active_model?.name || '尚未激活模型' }}</h2>
            <p>{{ active?.model_path || '请先上传或登记模型，选择推理设备并激活。' }}</p>
          </div>
          <div class="flex-gap">
            <div class="ws-info-item"><span class="info-label">当前选择</span><span class="info-value">{{ deviceLabel(active?.requested_device || 'auto') }}</span></div>
            <div class="ws-info-item"><span class="info-label">实际运行</span><span class="info-value">{{ active?.device || '-' }}</span></div>
            <div class="ws-info-item"><span class="info-label">初始化</span><span class="info-value">{{ warmupText }}</span></div>
            <div class="ws-info-item"><span class="info-label">CUDA</span><span class="info-value">{{ active?.cuda_available ? active.cuda_name || '可用' : '不可用' }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="ws-panel-2">
      <div class="ws-card">
        <div class="ws-card-header">推理设备切换</div>
        <div class="ws-card-body">
          <div class="flex-gap mb">
            <el-button v-for="option in displayDeviceOptions" :key="option.value" size="small" :type="selectedDevice === option.value ? 'primary' : 'default'" :disabled="!option.available || switchingDevice || !canManageModel" @click="selectedDevice = option.value">{{ option.label }}</el-button>
          </div>
          <div class="ws-info-item mb" style="border-color:var(--accent)">
            <span class="info-label">{{ deviceLabel(selectedDevice) }}</span>
            <span style="font-size:11px;color:var(--text-secondary)">{{ selectedDeviceDescription }}</span>
          </div>
          <el-button type="primary" :loading="switchingDevice" :disabled="!active?.active_model || !canManageModel" @click="switchDevice" style="width:100%">切换并预热</el-button>
          <p v-if="active?.warmup_error" class="text-danger" style="margin-top:6px">{{ active.warmup_error }}</p>
        </div>
      </div>

      <div class="ws-card">
        <div class="ws-card-header">导入模型</div>
        <div class="ws-card-body">
          <el-form :model="form" label-position="top">
            <el-form-item label="模型名称" required><el-input v-model="form.name" placeholder="输入模型显示名称" /></el-form-item>
            <el-form-item label="模型路径" required><el-input v-model="form.path" placeholder="绝对路径或 storage/models 下的文件名" /></el-form-item>
            <el-form-item label="版本号" required><el-input v-model="form.version" placeholder="输入版本标识" /></el-form-item>
            <el-button type="primary" :disabled="!canManageModel || !canRegisterModel" @click="register">登记路径</el-button>
          </el-form>
          <el-divider />
          <div class="flex-gap">
            <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel"><el-button>选择 .pt 文件</el-button></el-upload>
            <el-button type="primary" :disabled="!uploadFileRef" @click="upload">上传模型</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="ws-card" style="margin-top:12px">
      <div class="ws-card-header">
        <span>模型库</span>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
      <div class="ws-card-body">
        <el-table :data="models">
          <el-table-column label="序号" width="80"><template #default="{ $index }">{{ $index + 1 }}</template></el-table-column>
          <el-table-column prop="display_name" label="显示名称" min-width="150"><template #default="{ row }">{{ row.display_name || row.name }}</template></el-table-column>
          <el-table-column prop="name" label="后端名称" min-width="140" />
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="device" label="上次选择" width="100">
            <template #default="{ row }"><el-tag size="small" :type="row.device?.startsWith('cuda') ? 'success' : row.device === 'cpu' ? 'warning' : 'info'">{{ deviceLabel(row.device || 'auto') }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="90">
            <template #default="{ row }"><el-tag size="small" :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '运行中' : '未激活' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="path" label="路径" min-width="240">
            <template #default="{ row }"><el-tooltip :content="row.path" placement="top"><span style="font-family:var(--font-mono);font-size:11px;color:var(--text-secondary)">{{ row.path }}</span></el-tooltip></template>
          </el-table-column>
          <el-table-column label="操作" width="360" fixed="right">
            <template #default="{ row }">
              <div class="flex-gap">
                <el-button v-if="canManageModel" type="primary" size="small" :loading="activatingId === row.id" @click="activate(row.id)">激活</el-button>
                <el-button v-if="canManageModel" size="small" @click="openDisplayName(row)">改名</el-button>
                <el-button v-if="canManageModel" size="small" @click="openMapping(row)">映射</el-button>
                <el-button v-if="canManageModel" type="danger" size="small" :disabled="row.is_active" @click="remove(row.id)">删除</el-button>
                <el-tag v-else size="small" type="info">仅查看</el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="displayDialog" title="修改模型显示名称" width="420px">
      <el-input v-model="displayNameForm" placeholder="请输入前端显示名称" />
      <template #footer>
        <el-button @click="displayDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDisplayName">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="mappingDrawer" title="类别中英文对照" size="54%">
      <div class="flex-between mb">
        <span>{{ selectedModel?.display_name || selectedModel?.name }}</span>
        <el-button type="primary" size="small" @click="saveMapping">保存映射</el-button>
      </div>
      <el-table :data="mappingRows">
        <el-table-column prop="class_name" label="英文类别" min-width="160" />
        <el-table-column label="中文名称" min-width="220">
          <template #default="{ row }"><el-input v-model="row.class_zh" /></template>
        </el-table-column>
      </el-table>
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
const warmupText = computed(() => ({ cuda_ready: 'GPU 就绪', cpu_ready: 'CPU 就绪', pending: '等待初始化', failed: '失败', not_loaded: '未加载', idle: '未初始化' }[active.value?.warmup_status || 'idle'] || active.value?.warmup_status || '未初始化'))
const selectedDeviceDescription = computed(() => { if (selectedDevice.value === 'auto') return '系统自动优先使用 GPU，不可用时使用 CPU。'; if (selectedDevice.value === 'cpu') return '强制使用 CPU。'; return '强制使用指定 GPU，不可用时返回错误。' })

function deviceLabel(value: string) { if (!value || value === 'auto') return '自动'; if (value === 'cpu') return 'CPU'; if (value.startsWith('cuda')) return 'GPU'; return value }
function selectUploadModel(file: UploadFile) { uploadFileRef.value = file.raw || null }
async function load() { models.value = (await listModels()).items; active.value = await activeModel(); selectedDevice.value = active.value.requested_device || 'auto' }
async function register() { const name = form.name.trim(); const path = form.path.trim(); const version = form.version.trim(); if (!name || !path || !version) { ElMessage.warning('模型名称、路径和版本号不能为空'); return }; await registerModel({ name, path, version, class_names: [] }); Object.assign(form, { name: '', path: '', version: '' }); ElMessage.success('模型路径已登记'); await load() }
async function upload() { if (!uploadFileRef.value) return; await uploadModel(uploadFileRef.value); uploadFileRef.value = null; ElMessage.success('模型文件已上传'); await load() }
async function switchDevice() { switchingDevice.value = true; try { active.value = await switchModelDevice(selectedDevice.value); models.value = (await listModels()).items; ElMessage.success('设备已切换并预热') } finally { switchingDevice.value = false } }
async function activate(id: number) { activatingId.value = id; try { await activateModel(id, selectedDevice.value); ElMessage.success('模型已激活'); await load() } finally { activatingId.value = null } }
function openDisplayName(row: ModelInfo) { selectedModel.value = row; displayNameForm.value = row.display_name || row.name; displayDialog.value = true }
async function saveDisplayName() { if (!selectedModel.value) return; await updateModelDisplayName(selectedModel.value.id, displayNameForm.value); displayDialog.value = false; ElMessage.success('显示名称已更新'); await load() }
function openMapping(row: ModelInfo) { selectedModel.value = row; const classNames = parseJson<string[]>(row.class_names_json, []); const mapping = parseJson<Record<string, string>>(row.class_mapping_json, {}); mappingRows.value = classNames.map((className) => ({ class_name: className, class_zh: mapping[className] || className })); mappingDrawer.value = true }
async function saveMapping() { if (!selectedModel.value) return; const mapping = Object.fromEntries(mappingRows.value.map((row) => [row.class_name, row.class_zh])); await updateModelClassMapping(selectedModel.value.id, mapping); mappingDrawer.value = false; ElMessage.success('类别映射已保存'); await load() }
async function remove(id: number) { try { await ElMessageBox.confirm('确认删除这个未激活模型吗？', '删除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; await deleteModel(id); ElMessage.success('模型已删除'); await load() }
function parseJson<T>(text: string, fallback: T): T { try { return JSON.parse(text) as T } catch { return fallback } }
onMounted(load)
</script>
