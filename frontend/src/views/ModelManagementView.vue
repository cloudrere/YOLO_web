<template>
  <AppLayout>
    <section class="grid two">
      <el-card shadow="never" class="panel-card model-state">
        <template #header>当前激活模型</template>
        <div v-if="active">
          <p><strong>模型名称：</strong>{{ active.active_model?.name || '未激活' }}</p>
          <p><strong>引擎状态：</strong>{{ active.engine_loaded ? '已加载' : '未加载' }}</p>
          <p><strong>推理设备：</strong>{{ active.device }}</p>
          <p><strong>CUDA 可用：</strong>{{ active.cuda_available ? '是' : '否' }}</p>
          <p><strong>模型路径：</strong>{{ active.model_path || '-' }}</p>
        </div>
      </el-card>
      <el-card shadow="never" class="panel-card">
        <template #header>登记模型路径</template>
        <el-form :model="form" label-width="90px">
          <el-form-item label="模型名称"><el-input v-model="form.name" placeholder="例如 yolov8n" /></el-form-item>
          <el-form-item label="模型路径"><el-input v-model="form.path" placeholder="绝对路径或 storage/models 下的文件名" /></el-form-item>
          <el-form-item label="版本号"><el-input v-model="form.version" placeholder="例如 v1.0" /></el-form-item>
          <el-button type="primary" @click="register">登记模型</el-button>
        </el-form>
      </el-card>
    </section>
    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="toolbar"><span>模型列表</span><el-button @click="load">刷新</el-button></div>
      </template>
      <div class="inline-actions">
        <el-upload :auto-upload="false" :limit="1" :on-change="selectUploadModel">
          <el-button>选择模型文件</el-button>
        </el-upload>
        <el-button type="primary" :disabled="!uploadFileRef" @click="upload">上传模型</el-button>
      </div>
      <el-table :data="models">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="version" label="版本" />
        <el-table-column prop="device" label="设备" width="100" />
        <el-table-column prop="is_active" label="激活" width="100">
          <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="path" label="路径" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="activate(row.id)">激活</el-button>
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
