<template>
  <AppLayout>
    <!-- ═══ Hero 横幅 ═══ -->
    <section class="workstation-hero flex-between">
      <div>
        <span class="eyebrow dark">视觉检测</span>
        <h2>视频检测任务控制台</h2>
        <p>上传视频创建后台异步检测任务，支持暂停、继续和结束，检测结果按任务独立轮询更新。</p>
      </div>
      <div class="status-pills">
        <span class="pulse-dot" :class="running ? 'running' : task?.status === 'paused' ? 'warning' : task?.status === 'failed' ? 'danger' : task ? 'success' : 'idle'" />
        <el-tag v-if="task" :type="running ? (task.status === 'paused' ? 'warning' : '') : task.status === 'failed' ? 'danger' : 'success'" size="large">
          任务 {{ task.id }}
        </el-tag>
        <el-tag v-else size="large" type="info">未创建任务</el-tag>
        <el-tag size="large">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <!-- ═══ 双栏工作台 ═══ -->
    <section class="detection-workbench two-col">
      <!-- ── 左栏：参数面板 ── -->
      <aside class="panel-card">
        <div class="panel-section">
          <h3 class="panel-title">检测参数</h3>
          <div class="param-row">
            <label>置信度阈值 <span class="param-value">{{ params.confidence.toFixed(2) }}</span></label>
            <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          </div>
          <div class="param-row">
            <label>IoU 阈值 <span class="param-value">{{ params.iou.toFixed(2) }}</span></label>
            <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          </div>
          <div class="param-row switch-row">
            <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="running" />
          </div>
        </div>

        <div class="panel-section">
          <h3 class="panel-title">上传视频</h3>
          <el-upload class="upload-area" drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
            <div class="upload-placeholder">
              <span class="upload-icon">＋</span>
              <p>拖拽视频文件或点击选择</p>
              <small>支持 MP4 / AVI / MOV</small>
            </div>
          </el-upload>
        </div>

        <!-- 进度条 -->
        <div v-if="task" class="panel-section">
          <div class="progress-header flex-between">
            <span class="progress-label">任务进度</span>
            <span class="progress-percent">{{ Math.round(task.progress) }}%</span>
          </div>
          <el-progress
            :percentage="Math.round(task.progress)"
            :stroke-width="10"
            :status="task.status === 'failed' ? 'exception' : task.status === 'done' ? 'success' : undefined"
            :color="task.status === 'failed' ? 'var(--color-danger)' : 'var(--color-primary)'"
          />
        </div>

        <!-- 操作按钮行 -->
        <div class="split-actions three-col">
          <el-button type="primary" size="large" :disabled="!videoFile || loading || running" :loading="loading" @click="runVideo">
            开始检测
          </el-button>
          <el-button size="large" :disabled="!canPause" @click="togglePause">
            {{ task?.status === 'paused' ? '继续' : '暂停' }}
          </el-button>
          <el-button size="large" type="danger" :disabled="!canEnd" @click="endVideo">
            结束
          </el-button>
        </div>

        <p v-if="errorText" class="error-text">{{ errorText }}</p>
      </aside>

      <!-- ── 右栏：视频视口 ── -->
      <main class="panel-card">
        <!-- 视频标注流 -->
        <div class="panel-section">
          <h3 class="panel-title">视频标注流</h3>
          <div class="detect-canvas video-viewport" :class="{ 'has-stream': task }">
            <!-- 有任务：显示视频帧流 -->
            <img
              v-if="task"
              class="video-stream"
              :src="videoStreamUrl(task.id)"
              alt="视频检测标注流"
            />
            <!-- 扫描覆盖层（运行中） -->
            <div v-if="task && task.status === 'running'" class="scan-overlay">
              <div class="scan-line" />
            </div>
            <!-- 空态 -->
            <div v-else-if="!task" class="canvas-state empty">
              <div class="empty-icon-box">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none" style="opacity:0.25;">
                  <rect x="4" y="10" width="48" height="36" rx="6" stroke="currentColor" stroke-width="2" />
                  <polygon points="22,16 22,40 40,28" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round" />
                </svg>
              </div>
              <h3>等待视频任务</h3>
              <p>创建视频任务后在此查看标注帧流</p>
            </div>
          </div>
        </div>

        <!-- 进度指标 -->
        <div class="panel-section">
          <h3 class="panel-title">检测指标</h3>
          <div class="grid three" style="margin-bottom:0;">
            <div class="metric-card compact">
              <span class="metric-label">采样帧</span>
              <span class="metric-value">{{ summary?.frames_sampled ?? 0 }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">目标总数</span>
              <span class="metric-value">{{ summary?.results_count ?? 0 }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">进度</span>
              <span class="metric-value">{{ task ? Math.round(task.progress) + '%' : '0%' }}</span>
            </div>
          </div>
        </div>

        <!-- 任务状态摘要 -->
        <div v-if="task" class="panel-section">
          <h3 class="panel-title">任务状态</h3>
          <div class="task-status-strip">
            <div class="task-status-item">
              <span class="pulse-dot" :class="task.status === 'running' ? 'running' : task.status === 'paused' ? 'warning' : task.status === 'failed' ? 'danger' : task.status === 'done' ? 'success' : 'idle'" />
              <span class="task-status-label">{{ statusText(task.status) }}</span>
            </div>
          </div>
        </div>

        <el-empty v-if="!task" description="创建视频任务后显示检测流与指标" :image-size="80" />
      </main>
    </section>

    <!-- ═══ 底部：任务状态卡片 ═══ -->
    <section v-if="task" class="panel-card full">
      <div class="flex-between" style="margin-bottom:16px;">
        <div>
          <span class="eyebrow dark">任务详情</span>
          <h3 style="margin:4px 0 0;">视频任务状态</h3>
        </div>
        <el-button :disabled="!task" @click="clearResults">清除结果</el-button>
      </div>

      <div class="task-inspector">
        <el-progress
          :percentage="Math.round(task.progress)"
          :stroke-width="14"
          :status="task.status === 'failed' ? 'exception' : task.status === 'done' ? 'success' : undefined"
        />
        <div class="task-meta grid three" style="margin-top:16px;">
          <div class="metric-card compact">
            <span class="metric-label">状态</span>
            <span class="metric-value" style="font-size:18px;">{{ statusText(task.status) }}</span>
          </div>
          <div class="metric-card compact">
            <span class="metric-label">重试次数</span>
            <span class="metric-value" style="font-size:18px;">{{ task.retry_count }} / {{ task.max_retries }}</span>
          </div>
          <div class="metric-card compact">
            <span class="metric-label">任务 ID</span>
            <span class="metric-value" style="font-family:var(--font-mono);font-size:15px;">{{ task.id }}</span>
          </div>
        </div>
        <p v-if="task.error_message" class="error-text" style="margin-top:12px;">{{ task.error_message }}</p>
      </div>
    </section>

    <section v-else class="panel-card full" style="text-align:center;">
      <el-empty description="视频任务创建后显示进度和检测结果" :image-size="80" />
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

<style scoped>
/* ── Panel internals ── */
.panel-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--panel-pad);
}

.panel-section {
  margin-bottom: 20px;
}
.panel-section:last-child {
  margin-bottom: 0;
}

.panel-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: -0.01em;
}

.param-row {
  margin-bottom: 14px;
}
.param-row label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
}
.param-row.switch-row {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.param-value {
  font-family: var(--font-mono);
  color: var(--color-primary);
  font-weight: 700;
  font-size: 14px;
  background: var(--color-primary-soft);
  padding: 1px 8px;
  border-radius: 4px;
}

/* ── Upload ── */
.upload-area {
  width: 100%;
}
.upload-placeholder {
  padding: 8px 0;
}
.upload-placeholder .upload-icon {
  display: block;
  font-size: 32px;
  color: var(--color-primary-light);
  font-weight: 300;
  line-height: 1;
  margin-bottom: 4px;
}
.upload-placeholder p {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink);
}
.upload-placeholder small {
  color: var(--color-muted);
  font-size: 11px;
}

/* ── Progress ── */
.progress-header {
  margin-bottom: 8px;
}
.progress-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
}
.progress-percent {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 800;
  color: var(--color-primary);
}

/* ── Actions ── */
.split-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
.split-actions.three-col {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
}

/* ── Video viewport ── */
.video-viewport {
  position: relative;
  min-height: 320px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  overflow: hidden;
}
.video-viewport.has-stream {
  background: #0f172a;
  border-style: solid;
}

.video-stream {
  max-width: 100%;
  max-height: 480px;
  object-fit: contain;
  border-radius: var(--radius-sm);
  position: relative;
  z-index: 2;
}

/* ── Canvas empty state ── */
.canvas-state {
  display: grid;
  place-items: center;
  text-align: center;
  padding: 40px 20px;
  position: relative;
  z-index: 2;
}
.canvas-state.empty h3 {
  margin: 12px 0 4px;
  font-size: 17px;
  color: var(--color-ink);
}
.canvas-state.empty p {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
}

/* ── Metric compact ── */
.metric-card.compact {
  padding: 14px;
  text-align: center;
}
.metric-card.compact .metric-label {
  font-size: 11px;
}
.metric-card.compact .metric-value {
  font-size: 22px;
  margin-top: 2px;
}

/* ── Task status strip ── */
.task-status-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
}
.task-status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.task-status-label {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-ink);
}

/* ── Task inspector ── */
.task-inspector {
  padding: 8px 0;
}

/* ── Eyebrow ── */
.eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-primary);
  margin-bottom: 2px;
}
.eyebrow.dark {
  color: var(--color-muted);
}
</style>
