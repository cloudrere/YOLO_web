<template>
  <AppLayout>
    <section class="grid two">
      <el-card shadow="never">
        <template #header>Active Model</template>
        <div v-if="active">
          <p><strong>Model:</strong> {{ active.active_model?.name || 'None' }}</p>
          <p><strong>Engine Loaded:</strong> {{ active.engine_loaded }}</p>
          <p><strong>Device:</strong> {{ active.device }}</p>
          <p><strong>CUDA:</strong> {{ active.cuda_available }}</p>
          <p><strong>Path:</strong> {{ active.model_path || '-' }}</p>
        </div>
      </el-card>
      <el-card shadow="never">
        <template #header>Register Model Path</template>
        <el-form :model="form" label-width="90px">
          <el-form-item label="Name"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="Path"><el-input v-model="form.path" placeholder="absolute path or file under storage/models" /></el-form-item>
          <el-form-item label="Version"><el-input v-model="form.version" /></el-form-item>
          <el-button type="primary" @click="register">Register</el-button>
        </el-form>
      </el-card>
    </section>
    <el-card shadow="never">
      <template #header>
        <div class="toolbar"><span>Model List</span><el-button @click="load">Refresh</el-button></div>
      </template>
      <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel">
        <el-button>Choose model file</el-button>
      </el-upload>
      <el-button :disabled="!uploadFileRef" @click="upload">Upload Model</el-button>
      <el-table :data="models">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="version" label="Version" />
        <el-table-column prop="device" label="Device" width="100" />
        <el-table-column prop="is_active" label="Active" width="100" />
        <el-table-column prop="path" label="Path" />
        <el-table-column label="Actions" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="activate(row.id)">Activate</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { activateModel, activeModel, listModels, registerModel, uploadModel } from '@/api/model'
import type { ModelInfo } from '@/api/types'

const models = ref<ModelInfo[]>([])
const active = ref<Awaited<ReturnType<typeof activeModel>> | null>(null)
const uploadFileRef = ref<File | null>(null)
const form = reactive({ name: '', path: '', version: '' })

function selectUploadModel(file: UploadFile) {
  uploadFileRef.value = file.raw || null
}
async function load() {
  models.value = (await listModels()).items
  active.value = await activeModel()
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
async function activate(id: number) {
  await activateModel(id)
  await load()
}
onMounted(load)
</script>
