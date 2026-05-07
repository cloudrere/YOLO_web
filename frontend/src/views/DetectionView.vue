<template>
  <AppLayout>
    <section class="grid two">
      <el-card shadow="never">
        <template #header>Image Detection</template>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage">
          <p>Drop one image or click to select</p>
        </el-upload>
        <el-button type="primary" :disabled="!imageFile" :loading="imageLoading" @click="runImage">Run Image Detection</el-button>
      </el-card>
      <el-card shadow="never">
        <template #header>Batch Image Detection</template>
        <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove">
          <p>Drop multiple images or click to select</p>
        </el-upload>
        <el-button type="primary" :disabled="batchFiles.length === 0" :loading="batchLoading" @click="runBatch">Run Batch Detection</el-button>
      </el-card>
    </section>

    <section class="grid two">
      <el-card shadow="never">
        <template #header>Video Detection Task</template>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo">
          <p>Drop one video or click to select</p>
        </el-upload>
        <el-button type="primary" :disabled="!videoFile" :loading="videoLoading" @click="runVideo">Create Video Task</el-button>
        <div v-if="task" class="task-box">
          <el-progress :percentage="Math.round(task.progress)" />
          <p>Status: {{ task.status }} | Retry: {{ task.retry_count }}/{{ task.max_retries }}</p>
          <p v-if="task.error_message" class="error-text">{{ task.error_message }}</p>
          <img v-if="task.id" class="video-stream" :src="videoStreamUrl(task.id)" />
        </div>
      </el-card>
      <el-card shadow="never">
        <template #header>Latest Image Result</template>
        <DetectionResultTable :results="imageResult?.results || []" />
        <AnalysisPanel v-if="imageResult?.analysis" :analysis="imageResult.analysis" />
      </el-card>
    </section>

    <el-card v-if="batchResult" shadow="never">
      <template #header>Batch Results</template>
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
