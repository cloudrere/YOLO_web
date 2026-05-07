<template>
  <AppLayout>
    <section class="detect-hero glass-card">
      <div>
        <span class="eyebrow dark">统一推理入口</span>
        <h2>上传数据源，自动完成模型推理与结果入库</h2>
        <p>检测结果严格遵循 class / confidence / bbox 契约，类别名称来自当前激活模型。</p>
      </div>
    </section>

    <section class="grid three upload-grid">
      <el-card shadow="never" class="upload-card">
        <template #header>单张图片检测</template>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage">
          <p>拖拽图片到此处，或点击选择</p>
        </el-upload>
        <el-button type="primary" :disabled="!imageFile" :loading="imageLoading" @click="runImage">开始单图检测</el-button>
      </el-card>
      <el-card shadow="never" class="upload-card">
        <template #header>批量图片检测</template>
        <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove">
          <p>拖拽多张图片到此处，或点击选择</p>
        </el-upload>
        <el-button type="primary" :disabled="batchFiles.length === 0" :loading="batchLoading" @click="runBatch">开始批量检测</el-button>
      </el-card>
      <el-card shadow="never" class="upload-card">
        <template #header>视频异步检测</template>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo">
          <p>拖拽视频到此处，或点击选择</p>
        </el-upload>
        <el-button type="primary" :disabled="!videoFile" :loading="videoLoading" @click="runVideo">创建视频任务</el-button>
      </el-card>
    </section>

    <section class="grid two">
      <el-card shadow="never" class="panel-card">
        <template #header>最新单图检测结果</template>
        <DetectionResultTable :results="imageResult?.results || []" />
        <AnalysisPanel v-if="imageResult?.analysis" :analysis="imageResult.analysis" />
      </el-card>
      <el-card shadow="never" class="panel-card">
        <template #header>视频任务状态</template>
        <div v-if="task" class="task-box">
          <el-progress :percentage="Math.round(task.progress)" :stroke-width="14" />
          <p>状态：{{ statusText(task.status) }} | 重试：{{ task.retry_count }}/{{ task.max_retries }}</p>
          <p v-if="task.error_message" class="error-text">{{ task.error_message }}</p>
          <img v-if="task.id" class="video-stream" :src="videoStreamUrl(task.id)" />
        </div>
        <el-empty v-else description="尚未创建视频任务" />
      </el-card>
    </section>

    <el-card v-if="batchResult" shadow="never" class="panel-card">
      <template #header>批量检测结果</template>
      <el-collapse>
        <el-collapse-item v-for="item in batchResult.items" :key="item.file_name" :title="`${item.file_name} - ${item.status}`">
          <DetectionResultTable :results="item.results" />
          <AnalysisPanel v-if="item.analysis" :analysis="item.analysis" />
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import type { UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { detectBatch, detectImage, detectVideo, getTask, videoStreamUrl, type BatchDetectResult, type ImageDetectResult } from '@/api/detect'
import type { TaskInfo } from '@/api/types'

const imageFile = ref<File | null>(null)
const batchFiles = ref<File[]>([])
const videoFile = ref<File | null>(null)
const imageResult = ref<ImageDetectResult | null>(null)
const batchResult = ref<BatchDetectResult | null>(null)
const task = ref<TaskInfo | null>(null)
const imageLoading = ref(false)
const batchLoading = ref(false)
const videoLoading = ref(false)
let timer: number | undefined

function statusText(status: string) {
  return { pending: '等待中', running: '处理中', done: '已完成', failed: '失败' }[status] || status
}
function selectImage(file: UploadFile) {
  imageFile.value = file.raw || null
}
function selectVideo(file: UploadFile) {
  videoFile.value = file.raw || null
}
function collectBatch(_: UploadFile, files: UploadFile[]) {
  batchFiles.value = files.map((item) => item.raw).filter(Boolean) as File[]
}
function collectBatchRemove(_: UploadFile, files: UploadFile[]) {
  batchFiles.value = files.map((item) => item.raw).filter(Boolean) as File[]
}
async function runImage() {
  if (!imageFile.value) return
  imageLoading.value = true
  try {
    imageResult.value = await detectImage(imageFile.value)
  } finally {
    imageLoading.value = false
  }
}
async function runBatch() {
  batchLoading.value = true
  try {
    batchResult.value = await detectBatch(batchFiles.value)
  } finally {
    batchLoading.value = false
  }
}
async function runVideo() {
  if (!videoFile.value) return
  videoLoading.value = true
  try {
    const created = await detectVideo(videoFile.value)
    task.value = await getTask(created.task_id)
    timer = window.setInterval(async () => {
      if (!task.value) return
      task.value = await getTask(task.value.id)
      if (['done', 'failed'].includes(task.value.status)) window.clearInterval(timer)
    }, 1500)
  } finally {
    videoLoading.value = false
  }
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
