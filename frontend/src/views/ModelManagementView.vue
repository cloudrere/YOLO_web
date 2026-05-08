<template>
  <AppLayout>
    <section class="model-command-center panel-card">
      <div class="model-command-main">
        <span class="eyebrow dark">模型控制室</span>
        <h2>{{ active?.active_model?.name || '尚未激活模型' }}</h2>
        <p>{{ active?.model_path || '请先上传或登记模型，然后选择推理设备并激活。' }}</p>
      </div>
      <div class="model-command-stats">
        <div><span>当前选择</span><strong>{{ deviceLabel(active?.requested_device || 'auto') }}</strong></div>
        <div><span>实际运行</span><strong>{{ active?.device || '-' }}</strong></div>
        <div><span>初始化</span><strong>{{ warmupText }}</strong></div>
        <div><span>CUDA</span><strong>{{ active?.cuda_available ? active.cuda_name || '可用' : '不可用' }}</strong></div>
      </div>
    </section>

    <section class="model-control-layout">
      <el-card shadow="never" class="panel-card device-control-panel">
        <template #header>推理设备切换</template>
        <div class="device-switcher">
          <el-button
            v-for="option in displayDeviceOptions"
            :key="option.value"
            :type="selectedDevice === option.value ? 'primary' : 'default'"
            :disabled="!option.available || switchingDevice"
            @click="selectedDevice = option.value"
          >
            {{ option.label }}
          </el-button>
        </div>
        <div class="device-detail-card" :class="selectedDevice.startsWith('cuda') ? 'gpu' : selectedDevice === 'cpu' ? 'cpu' : 'auto'">
          <strong>{{ deviceLabel(selectedDevice) }}</strong>
          <span>{{ selectedDeviceDescription }}</span>
        </div>
        <el-button class="full" type="primary" :loading="switchingDevice" :disabled="!active?.active_model" @click="switchDevice">
          切换并预热
        </el-button>
        <p v-if="active?.warmup_error" class="error-text">{{ active.warmup_error }}</p>
      </el-card>

      <el-card shadow="never" class="panel-card model-register-card compact-form-card">
        <template #header>导入模型</template>
        <el-form :model="form" label-position="top">
          <el-form-item label="模型名称"><el-input v-model="form.name" placeholder="输入模型显示名称" /></el-form-item>
          <el-form-item label="模型路径"><el-input v-model="form.path" placeholder="绝对路径或 storage/models 下的文件名" /></el-form-item>
          <el-form-item label="版本号"><el-input v-model="form.version" placeholder="输入版本标识" /></el-form-item>
          <div class="form-actions">
            <el-button type="primary" @click="register">登记路径</el-button>
          </div>
        </el-form>
        <div class="model-upload-zone">
          <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel">
            <el-button>选择 .pt 文件</el-button>
          </el-upload>
          <el-button type="primary" :disabled="!uploadFileRef" @click="upload">上传模型</el-button>
        </div>
      </el-card>
    </section>

    <el-card shadow="never" class="panel-card model-library-panel">
      <template #header>
        <div class="toolbar"><span>模型库</span><el-button @click="load">刷新</el-button></div>
      </template>
      <div class="table-scroll model-table-shell">
        <el-table :data="models" class="model-table">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="device" label="上次选择" width="130">
            <template #default="{ row }"><el-tag :type="row.device?.startsWith('cuda') ? 'success' : row.device === 'cpu' ? 'warning' : 'info'">{{ deviceLabel(row.device || 'auto') }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="110">
            <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '运行中' : '未激活' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="path" label="路径" min-width="280" />
          <el-table-column label="操作" width="170">
            <template #default="{ row }">
              <el-button type="primary" size="small" :loading="activatingId === row.id" @click="activate(row.id)">按当前设备激活</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { activateModel, activeModel, listModels, registerModel, switchModelDevice, uploadModel } from '@/api/model'
import type { ModelDeviceInfo, ModelEngineState, ModelInfo } from '@/api/types'

const models = ref<ModelInfo[]>([])
const active = ref<ModelEngineState | null>(null)
const uploadFileRef = ref<File | null>(null)
const activatingId = ref<number | null>(null)
const switchingDevice = ref(false)
const selectedDevice = ref('auto')
const form = reactive({ name: '', path: '', version: '' })

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
const selectedDeviceDescription = computed(() => {
  if (selectedDevice.value === 'auto') return '系统自动优先使用可用 GPU，不可用时使用 CPU。'
  if (selectedDevice.value === 'cpu') return '强制使用 CPU，适合调试或显存不足时运行。'
  return '强制使用指定 GPU，CUDA 不可用时会直接返回错误。'
})

function deviceLabel(value: string) {
  if (!value || value === 'auto') return '自动'
  if (value === 'cpu') return 'CPU'
  if (value.startsWith('cuda')) return value.toUpperCase()
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
  await registerModel({ ...form, class_names: [] })
  Object.assign(form, { name: '', path: '', version: '' })
  await load()
}
async function upload() {
  if (!uploadFileRef.value) return
  await uploadModel(uploadFileRef.value)
  uploadFileRef.value = null
  await load()
}
async function switchDevice() {
  switchingDevice.value = true
  try {
    active.value = await switchModelDevice(selectedDevice.value)
    models.value = (await listModels()).items
  } finally {
    switchingDevice.value = false
  }
}
async function activate(id: number) {
  activatingId.value = id
  try {
    await activateModel(id, selectedDevice.value)
    await load()
  } finally {
    activatingId.value = null
  }
}
onMounted(load)
</script>
