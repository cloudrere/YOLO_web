<template>
  <AppLayout>
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow dark">视频文件检测</span>
        <h2>异步视频抽帧检测</h2>
        <p>上传视频创建后台任务，支持暂停、继续和结束，检测结果按任务独立轮询。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="task ? 'success' : 'info'">{{ task ? `任务 ${task.id}` : '未创建任务' }}</el-tag>
        <el-tag>{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench single-flow">
      <aside class="detection-control-rail panel-card">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="running" />
        </div>
        <div class="mode-config">
          <h3>上传视频</h3>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
            <p>选择视频文件后创建检测任务</p>
          </el-upload>
          <el-progress v-if="task" :percentage="Math.round(task.progress)" :stroke-width="12" />
          <div class="split-actions three-actions">
            <el-button type="primary" size="large" :disabled="!videoFile || loading || running" :loading="loading" @click="runVideo">开始</el-button>
            <el-button size="large" :disabled="!canPause" @click="togglePause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
            <el-button size="large" type="danger" :disabled="!canEnd" @click="endVideo">结束</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <main class="detection-preview-stage panel-card">
        <div class="preview-header">
          <div><span>视频标注流</span><strong>{{ task ? statusText(task.status) : '等待视频任务' }}</strong></div>
          <el-tag :type="running ? 'success' : task?.status === 'paused' ? 'warning' : task?.status === 'failed' ? 'danger' : 'info'">{{ task ? statusText(task.status) : '待创建' }}</el-tag>
        </div>
        <div class="preview-canvas">
          <img v-if="task" class="video-stream" :src="videoStreamUrl(task.id)" alt="视频检测标注流" />
          <el-empty v-else description="创建视频任务后显示标注帧流" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ summary?.frames_sampled ?? 0 }}</strong><span>采样帧</span></div>
          <div><strong>{{ summary?.results_count ?? 0 }}</strong><span>目标数</span></div>
          <div><strong>{{ task ? `${Math.round(task.progress)}%` : '0%' }}</strong><span>进度</span></div>
        </div>
      </main>
    </section>

    <section class="detection-inspector panel-card">
      <div class="inspector-header">
        <div><span class="eyebrow dark">任务详情</span><h3>视频任务状态</h3></div>
        <el-button :disabled="!task" @click="clearResults">清除结果</el-button>
      </div>
      <div v-if="task" class="task-inspector">
        <el-progress :percentage="Math.round(task.progress)" :stroke-width="14" />
        <div class="task-meta">
          <span>状态：{{ statusText(task.status) }}</span>
          <span>重试：{{ task.retry_count }}/{{ task.max_retries }}</span>
          <span>任务 ID：{{ task.id }}</span>
        </div>
        <p v-if="task.error_message" class="error-text">{{ task.error_message }}</p>
      </div>
      <el-empty v-else description="视频任务创建后显示进度和检测结果" />
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { controlTask, detectVideo, getTask, videoStreamUrl } from '@/api/detect'
import type { TaskInfo } from '@/api/types'

interface VideoSummary {
  frames_processed?: number
  frames_sampled?: number
  results_count?: number
}

const videoFile = ref<File | null>(null)
const task = ref<TaskInfo | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
let timer: number | undefined

const running = computed(() => Boolean(task.value && ['pending', 'running', 'paused'].includes(task.value.status)))
const canPause = computed(() => Boolean(task.value && ['running', 'paused'].includes(task.value.status)))
const canEnd = computed(() => Boolean(task.value && ['pending', 'running', 'paused'].includes(task.value.status)))
const summary = computed<VideoSummary | null>(() => {
  if (!task.value?.result_json) return null
  try {
    return JSON.parse(task.value.result_json) as VideoSummary
  } catch {
    return null
  }
})

function statusText(status: string) {
  return { pending: '等待中', running: '处理中', paused: '已暂停', cancelled: '已结束', done: '已完成', failed: '失败' }[status] || status
}
function selectVideo(file: UploadFile) {
  videoFile.value = file.raw || null
}
function removeVideo() {
  videoFile.value = null
}
async function runVideo() {
  if (!videoFile.value) return
  loading.value = true
  errorText.value = ''
  window.clearInterval(timer)
  try {
    const created = await detectVideo(videoFile.value, { ...params })
    task.value = await getTask(created.task_id)
    ElMessage.success('视频检测任务已创建')
    timer = window.setInterval(async () => {
      if (!task.value) return
      task.value = await getTask(task.value.id)
      if (['done', 'failed', 'cancelled'].includes(task.value.status)) window.clearInterval(timer)
    }, 1500)
  } catch (error: any) {
    errorText.value = error?.message || '视频检测任务创建失败'
    ElMessage.error(errorText.value)
  } finally {
    loading.value = false
  }
}
async function togglePause() {
  if (!task.value) return
  task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause')
  ElMessage.info(task.value.status === 'paused' ? '视频任务已暂停' : '视频任务已继续')
}
async function endVideo() {
  if (!task.value) return
  try {
    await ElMessageBox.confirm('确认结束当前视频检测任务吗？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' })
  } catch {
    return
  }
  task.value = await controlTask(task.value.id, 'cancel')
  window.clearInterval(timer)
  ElMessage.warning('视频检测已结束')
}
async function clearResults() {
  try {
    await ElMessageBox.confirm('确认清除当前视频任务和结果展示吗？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' })
  } catch {
    return
  }
  task.value = null
  errorText.value = ''
  window.clearInterval(timer)
  ElMessage.success('视频任务结果已清除')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
