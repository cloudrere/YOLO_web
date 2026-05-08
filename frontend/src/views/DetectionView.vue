<template>
  <AppLayout>
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow dark">智能检测工作台</span>
        <h2>{{ modeMeta.title }}</h2>
        <p>{{ modeMeta.description }}</p>
      </div>
      <div class="status-pills">
        <el-tag>{{ modeMeta.tag }}</el-tag>
        <el-tag :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '上传到历史记录' : '仅本地检测' }}</el-tag>
        <el-tag type="info">置信度 {{ params.confidence.toFixed(2) }} / IoU {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench">
      <aside class="detection-control-rail panel-card">
        <div class="mode-tabs">
          <button v-for="option in modeOptions" :key="option.value" :class="{ active: mode === option.value }" @click="mode = option.value">
            <strong>{{ option.label }}</strong>
            <span>{{ option.hint }}</span>
          </button>
        </div>

        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" />
        </div>

        <div class="mode-config">
          <template v-if="mode === 'image'">
            <h3>单张图片检测</h3>
            <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage">
              <p>选择一张图片生成标注结果</p>
            </el-upload>
            <div class="split-actions">
              <el-button type="primary" size="large" :disabled="!imageFile" :loading="imageLoading" @click="runImage">开始检测</el-button>
              <el-button size="large" @click="clearResults">清除</el-button>
            </div>
          </template>

          <template v-else-if="mode === 'batch'">
            <h3>批量图片检测</h3>
            <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove">
              <p>选择多张图片批量生成标注图</p>
            </el-upload>
            <div class="control-note">已选择 {{ batchFiles.length }} 张图片</div>
            <el-progress v-if="batchLoading || batchResult" :percentage="batchProgress" :stroke-width="12" />
            <div class="split-actions three-actions">
              <el-button type="primary" size="large" :disabled="batchFiles.length === 0 || batchLoading" @click="runBatch">开始</el-button>
              <el-button size="large" :disabled="!batchLoading" @click="toggleBatchPause">{{ batchPaused ? '继续' : '暂停' }}</el-button>
              <el-button size="large" type="danger" :disabled="!batchLoading && !batchResult" @click="endBatch">结束</el-button>
            </div>
          </template>

          <template v-else-if="mode === 'video'">
            <h3>视频文件检测</h3>
            <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo">
              <p>上传视频后创建异步检测任务</p>
            </el-upload>
            <el-progress v-if="task" :percentage="Math.round(task.progress)" :stroke-width="12" />
            <div class="split-actions three-actions">
              <el-button type="primary" size="large" :disabled="!videoFile || videoLoading" :loading="videoLoading" @click="runVideo">开始</el-button>
              <el-button size="large" :disabled="!canPauseVideo" @click="toggleVideoPause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
              <el-button size="large" type="danger" :disabled="!task || ['done', 'failed', 'cancelled'].includes(task.status)" @click="endVideo">结束</el-button>
            </div>
          </template>

          <template v-else>
            <h3>实时视频流检测</h3>
            <el-input v-model="realtimeSource" size="large" placeholder="摄像头 0 或 RTSP/HTTP 地址" />
            <div class="split-actions three-actions">
              <el-button type="primary" size="large" :disabled="!!realtimeUrl" @click="startRealtime">开始</el-button>
              <el-button size="large" :disabled="!realtimeUrl && !realtimePaused" @click="toggleRealtimePause">{{ realtimePaused ? '继续' : '暂停' }}</el-button>
              <el-button size="large" type="danger" :disabled="!realtimeUrl && !realtimePaused" @click="stopRealtime">结束</el-button>
            </div>
            <div class="control-note">暂停会断开当前 MJPEG 连接，继续时按当前参数重新连接。</div>
          </template>
        </div>
      </aside>

      <main class="detection-preview-stage panel-card">
        <div class="preview-header">
          <div>
            <span>{{ modeMeta.previewLabel }}</span>
            <strong>{{ previewTitle }}</strong>
          </div>
          <el-tag :type="previewTagType">{{ previewStatus }}</el-tag>
        </div>

        <div class="preview-canvas">
          <div v-if="mode === 'image' && (imageResult?.original_url || imageResult?.result_url)" class="compare-grid">
            <figure><img v-if="imageResult.original_url" :src="mediaUrl(imageResult.original_url)" alt="原图" /><figcaption>原图</figcaption></figure>
            <figure><img v-if="imageResult.result_url" :src="mediaUrl(imageResult.result_url)" alt="检测图" /><figcaption>检测图</figcaption></figure>
          </div>
          <img v-else-if="mode === 'video' && task" class="video-stream" :src="videoStreamUrl(task.id)" alt="视频检测标注流" />
          <img v-else-if="mode === 'realtime' && realtimeUrl" class="video-stream" :src="realtimeUrl" alt="实时视频流检测" />
          <div v-else-if="mode === 'batch' && batchResult?.items.length" class="batch-preview-wall">
            <img v-for="item in batchResult.items.slice(0, 6)" :key="item.file_name" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
          </div>
          <el-empty v-else :description="modeMeta.empty" />
        </div>

        <div class="preview-metrics">
          <div><strong>{{ metricPrimary }}</strong><span>{{ metricPrimaryLabel }}</span></div>
          <div><strong>{{ metricSecondary }}</strong><span>{{ metricSecondaryLabel }}</span></div>
          <div><strong>{{ metricTertiary }}</strong><span>{{ metricTertiaryLabel }}</span></div>
        </div>
      </main>
    </section>

    <section class="detection-inspector panel-card">
      <div class="inspector-header">
        <div>
          <span class="eyebrow dark">结果详情</span>
          <h3>{{ modeMeta.inspectorTitle }}</h3>
        </div>
        <el-button @click="clearResults">清除结果</el-button>
      </div>

      <template v-if="mode === 'image'">
        <DetectionResultTable :results="imageResult?.results || []" />
        <AnalysisPanel v-if="imageResult?.analysis" :analysis="imageResult.analysis" />
      </template>

      <template v-else-if="mode === 'batch'">
        <div v-if="batchResult" class="batch-result-grid compact-batch-grid">
          <article v-for="item in batchResult.items" :key="item.file_name" class="batch-result-card">
            <div class="compare-grid batch-compare">
              <figure><img v-if="item.original_url" :src="mediaUrl(item.original_url)" :alt="item.file_name" /><figcaption>原图</figcaption></figure>
              <figure><img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" /><figcaption>检测图</figcaption></figure>
            </div>
            <div class="batch-card-body">
              <div class="toolbar">
                <strong>{{ item.file_name }}</strong>
                <el-tag :type="item.status === 'done' ? 'success' : 'danger'">{{ statusText(item.status) }}</el-tag>
              </div>
              <DetectionResultTable :results="item.results" />
            </div>
          </article>
        </div>
        <el-empty v-else description="批量检测完成后显示每张图片结果" />
      </template>

      <template v-else-if="mode === 'video'">
        <div v-if="task" class="task-inspector">
          <el-progress :percentage="Math.round(task.progress)" :stroke-width="14" />
          <div class="task-meta">
            <span>状态：{{ statusText(task.status) }}</span>
            <span>重试：{{ task.retry_count }}/{{ task.max_retries }}</span>
            <span>任务 ID：{{ task.id }}</span>
          </div>
          <p v-if="task.error_message" class="error-text">{{ task.error_message }}</p>
          <AnalysisPanel v-if="videoSummary?.analysis" :analysis="videoSummary.analysis" />
        </div>
        <el-empty v-else description="视频任务创建后显示进度和分析结果" />
      </template>

      <template v-else>
        <div class="realtime-guide">
          <strong>{{ realtimeStatusText }}</strong>
          <p>来源：{{ realtimeSource || '0' }}；运行时长：{{ realtimeElapsed }} 秒；协议：MJPEG。</p>
        </div>
      </template>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import type { UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import {
  apiMediaUrl,
  controlTask,
  detectBatch,
  detectImage,
  detectVideo,
  getTask,
  realtimeStreamUrl,
  videoStreamUrl,
  type BatchDetectResult,
  type DetectParameters,
  type ImageDetectResult,
} from '@/api/detect'
import type { AIAnalysis, DetectionResult, TaskInfo } from '@/api/types'

type DetectionMode = 'image' | 'batch' | 'video' | 'realtime'

interface VideoSummary {
  frames_processed?: number
  frames_sampled?: number
  results_count?: number
  analysis?: AIAnalysis
}

const mode = ref<DetectionMode>('image')
const imageFile = ref<File | null>(null)
const batchFiles = ref<File[]>([])
const videoFile = ref<File | null>(null)
const imageResult = ref<ImageDetectResult | null>(null)
const batchResult = ref<BatchDetectResult | null>(null)
const task = ref<TaskInfo | null>(null)
const imageLoading = ref(false)
const batchLoading = ref(false)
const batchPaused = ref(false)
const batchProgress = ref(0)
const batchEnded = ref(false)
const videoLoading = ref(false)
const realtimeSource = ref('0')
const realtimeUrl = ref('')
const realtimePaused = ref(false)
const realtimeStartedAt = ref<number | null>(null)
const realtimeTick = ref(0)
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
let timer: number | undefined
let realtimeTimer: number | undefined

const modeOptions: Array<{ value: DetectionMode; label: string; hint: string }> = [
  { value: 'image', label: '单图', hint: '快速验证一张图' },
  { value: 'batch', label: '批量', hint: '多图集中处理' },
  { value: 'video', label: '视频', hint: '异步任务预览' },
  { value: 'realtime', label: '实时', hint: '摄像头/流检测' },
]
const modeMeta = computed(() => {
  const map = {
    image: {
      title: '单图检测与标注预览',
      description: '上传图片后直接展示原图、检测图、目标数量与 AI 分析。',
      tag: '图片模式',
      previewLabel: '原图 / 检测图',
      empty: '上传单张图片后显示对比图',
      inspectorTitle: '单图结构化结果',
    },
    batch: {
      title: '批量图片检测',
      description: '多张图片统一推理，支持开始、暂停、继续和结束批量队列。',
      tag: '批量模式',
      previewLabel: '批量预览',
      empty: '批量检测完成后显示缩略图墙',
      inspectorTitle: '批量图片结果',
    },
    video: {
      title: '视频文件异步检测',
      description: '上传视频后后台抽帧推理，支持暂停、继续和结束任务。',
      tag: '视频模式',
      previewLabel: '视频标注流',
      empty: '创建视频任务后显示标注视频流',
      inspectorTitle: '视频任务状态',
    },
    realtime: {
      title: '实时视频流检测',
      description: '接入本机摄像头、RTSP 或 HTTP(S) 流，实时返回标注画面。',
      tag: '实时模式',
      previewLabel: '实时画面',
      empty: '连接实时流后显示标注画面',
      inspectorTitle: '实时状态面板',
    },
  }
  return map[mode.value]
})
const requestParams = computed<DetectParameters>(() => ({ confidence: params.confidence, iou: params.iou, save_history: params.save_history }))
const videoSummary = computed<VideoSummary | null>(() => {
  if (!task.value?.result_json) return null
  try {
    return JSON.parse(task.value.result_json) as VideoSummary
  } catch {
    return null
  }
})
const previewTitle = computed(() => {
  if (mode.value === 'image') return imageResult.value ? '检测完成' : '等待图片'
  if (mode.value === 'batch') return batchResult.value ? `${batchResult.value.items.length} 张图片` : batchLoading.value ? '批量处理中' : '等待批量任务'
  if (mode.value === 'video') return task.value ? statusText(task.value.status) : '等待视频任务'
  return realtimeUrl.value ? '实时检测中' : realtimePaused.value ? '已暂停' : '未连接'
})
const previewStatus = computed(() => {
  if (mode.value === 'image') return imageLoading.value ? '检测中' : imageResult.value ? '已完成' : '待上传'
  if (mode.value === 'batch') return batchLoading.value ? (batchPaused.value ? '已暂停' : '检测中') : batchResult.value ? '已完成' : '待上传'
  if (mode.value === 'video') return task.value ? statusText(task.value.status) : '待创建'
  return realtimeUrl.value ? '检测中' : realtimePaused.value ? '已暂停' : '未连接'
})
const previewTagType = computed(() => (['已完成', '检测中', '处理中', '运行中'].includes(previewStatus.value) ? 'success' : previewStatus.value === '已暂停' ? 'warning' : 'info'))
const metricPrimary = computed(() => {
  if (mode.value === 'image') return imageResult.value?.results.length ?? 0
  if (mode.value === 'batch') return batchResult.value?.items.length ?? batchFiles.value.length
  if (mode.value === 'video') return videoSummary.value?.frames_sampled ?? 0
  return realtimeUrl.value ? 'ON' : 'OFF'
})
const metricPrimaryLabel = computed(() => ({ image: '目标数', batch: '图片数', video: '采样帧', realtime: '连接' })[mode.value])
const metricSecondary = computed(() => {
  if (mode.value === 'image') return imageResult.value?.duration_ms ?? 0
  if (mode.value === 'batch') return batchResult.value?.items.reduce((sum, item) => sum + item.results.length, 0) ?? 0
  if (mode.value === 'video') return videoSummary.value?.results_count ?? 0
  return realtimeSource.value || '0'
})
const metricSecondaryLabel = computed(() => ({ image: '耗时(ms)', batch: '目标数', video: '目标数', realtime: '来源' })[mode.value])
const metricTertiary = computed(() => {
  if (mode.value === 'image') return topClass(imageResult.value?.results || [])
  if (mode.value === 'batch') return `${batchProgress.value}%`
  if (mode.value === 'video') return task.value ? `${Math.round(task.value.progress)}%` : '0%'
  return realtimeElapsed.value
})
const metricTertiaryLabel = computed(() => ({ image: '高频类别', batch: '进度', video: '进度', realtime: '运行秒数' })[mode.value])
const canPauseVideo = computed(() => Boolean(task.value && ['running', 'paused'].includes(task.value.status)))
const realtimeElapsed = computed(() => {
  realtimeTick.value
  return realtimeStartedAt.value ? Math.floor((Date.now() - realtimeStartedAt.value) / 1000) : 0
})
const realtimeStatusText = computed(() => (realtimeUrl.value ? '实时检测正在运行' : realtimePaused.value ? '实时检测已暂停' : '实时检测未连接'))

function mediaUrl(path: string) {
  return apiMediaUrl(path)
}
function statusText(status: string) {
  return { pending: '等待中', running: '处理中', paused: '已暂停', cancelled: '已结束', done: '已完成', failed: '失败' }[status] || status
}
function topClass(results: DetectionResult[]) {
  if (!results.length) return '无'
  const counts = results.reduce<Record<string, { count: number; label: string }>>((acc, item) => {
    acc[item.class] = acc[item.class] || { count: 0, label: item.class_zh || item.class }
    acc[item.class].count += 1
    return acc
  }, {})
  return Object.values(counts).sort((a, b) => b.count - a.count)[0].label
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
    imageResult.value = await detectImage(imageFile.value, requestParams.value)
  } finally {
    imageLoading.value = false
  }
}
async function runBatch() {
  batchLoading.value = true
  batchPaused.value = false
  batchEnded.value = false
  batchResult.value = { items: [], parameters: requestParams.value }
  batchProgress.value = 0
  try {
    for (let index = 0; index < batchFiles.value.length; index += 1) {
      if (batchEnded.value) break
      while (batchPaused.value && !batchEnded.value) await wait(200)
      const result = await detectBatch([batchFiles.value[index]], requestParams.value)
      batchResult.value.items.push(...result.items)
      batchProgress.value = Math.round(((index + 1) / batchFiles.value.length) * 100)
    }
  } finally {
    batchLoading.value = false
  }
}
function toggleBatchPause() {
  batchPaused.value = !batchPaused.value
}
function endBatch() {
  batchEnded.value = true
  batchPaused.value = false
  batchLoading.value = false
}
async function runVideo() {
  if (!videoFile.value) return
  videoLoading.value = true
  window.clearInterval(timer)
  try {
    const created = await detectVideo(videoFile.value, requestParams.value)
    task.value = await getTask(created.task_id)
    timer = window.setInterval(async () => {
      if (!task.value) return
      task.value = await getTask(task.value.id)
      if (['done', 'failed', 'cancelled'].includes(task.value.status)) window.clearInterval(timer)
    }, 1500)
  } finally {
    videoLoading.value = false
  }
}
async function toggleVideoPause() {
  if (!task.value) return
  task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause')
}
async function endVideo() {
  if (!task.value) return
  task.value = await controlTask(task.value.id, 'cancel')
  window.clearInterval(timer)
}
function startRealtime() {
  realtimeUrl.value = realtimeStreamUrl(realtimeSource.value, requestParams.value)
  realtimePaused.value = false
  realtimeStartedAt.value = Date.now()
  window.clearInterval(realtimeTimer)
  realtimeTimer = window.setInterval(() => {
    realtimeTick.value += 1
  }, 1000)
}
function toggleRealtimePause() {
  if (realtimeUrl.value) {
    realtimeUrl.value = ''
    realtimePaused.value = true
    return
  }
  startRealtime()
}
function stopRealtime() {
  realtimeUrl.value = ''
  realtimePaused.value = false
  realtimeStartedAt.value = null
  window.clearInterval(realtimeTimer)
}
function clearResults() {
  imageResult.value = null
  batchResult.value = null
  task.value = null
  batchProgress.value = 0
  batchEnded.value = true
  window.clearInterval(timer)
  stopRealtime()
}
function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
onBeforeUnmount(() => {
  window.clearInterval(timer)
  window.clearInterval(realtimeTimer)
  stopRealtime()
})
</script>
