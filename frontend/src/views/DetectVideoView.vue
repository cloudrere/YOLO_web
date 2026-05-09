<template>
  <AppLayout>
    <section class="detection-status-strip">
      <div>
        <span class="eyebrow dark">视频检测工作区</span>
        <h2>异步视频抽帧分析</h2>
        <p>上传视频创建后台异步任务，实时显示标注帧流和进度，支持暂停继续和结束控制。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="task ? 'success' : 'info'">{{ task ? `任务 #${task.id}` : '未创建' }}</el-tag>
        <el-tag>置信度 {{ params.confidence.toFixed(2) }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench two-col">
      <!-- 左侧：参数和上传 -->
      <aside class="detection-control-rail workstation-panel">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度 {{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <label>IoU 阈值 {{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <div style="margin-top: 14px;">
            <el-switch v-model="params.save_history" active-text="存入历史" inactive-text="仅本地" :disabled="running" />
          </div>
        </div>
        <div style="padding: 16px; border-top: 1px solid var(--border-soft);">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: var(--color-primary-deep);">上传视频</h3>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
            <p style="font-size: 13px; color: var(--color-muted);">选择视频文件创建检测任务</p>
          </el-upload>
          <div class="split-actions three-actions" style="margin-top: 14px;">
            <el-button type="primary" size="small" :disabled="!videoFile || loading || running" :loading="loading" @click="runVideo">创建</el-button>
            <el-button size="small" :disabled="!canPause" @click="togglePause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
            <el-button size="small" type="danger" :disabled="!canEnd" @click="endVideo">结束</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <!-- 右侧：视频预览 + 任务控制 -->
      <main class="detection-preview-stage workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">视频分析台</span><strong style="display: block; font-size: 20px; margin-top: 2px; color: var(--color-primary-deep);">{{ task ? statusText(task.status) : '等待视频' }}</strong></div>
          <el-tag :type="running ? 'success' : task?.status === 'paused' ? 'warning' : 'info'" size="small">{{ task ? statusText(task.status) : '待创建' }}</el-tag>
        </div>
        <div class="preview-canvas" style="background: #1a202c;">
          <img v-if="task" class="video-stream" :src="videoStreamUrl(task.id)" alt="视频检测标注流" style="max-height: 560px;" />
          <el-empty v-else description="创建任务后显示标注帧流" />
        </div>
        <div class="preview-metrics" style="margin-top: 14px;">
          <div><strong>{{ summary?.frames_sampled ?? 0 }}</strong><span>采样帧数</span></div>
          <div><strong>{{ summary?.results_count ?? 0 }}</strong><span>检测目标</span></div>
          <div><strong>{{ task ? Math.round(task.progress) + '%' : '0%' }}</strong><span>任务进度</span></div>
        </div>

        <!-- 任务详情区 -->
        <div v-if="task" style="margin-top: 16px; padding: 16px; border: 1px solid var(--border-soft); border-radius: 12px; background: var(--color-surface-alt);">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: var(--color-primary-deep);">任务状态</h3>
          <el-progress :percentage="Math.round(task.progress)" :stroke-width="12" />
          <div style="display: flex; flex-wrap: wrap; gap: 16px; margin-top: 12px; color: var(--color-muted); font-size: 13px;">
            <span>状态：{{ statusText(task.status) }}</span>
            <span>重试：{{ task.retry_count }}/{{ task.max_retries }}</span>
            <span>ID：{{ task.id }}</span>
          </div>
          <p v-if="task.error_message" class="error-text">{{ task.error_message }}</p>
        </div>
      </main>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { controlTask, detectVideo, getTask, videoStreamUrl } from '@/api/detect'
import type { TaskInfo } from '@/api/types'

interface VideoSummary { frames_processed?: number; frames_sampled?: number; results_count?: number }

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
  try { return JSON.parse(task.value.result_json) as VideoSummary } catch { return null }
})

function statusText(status: string) {
  return { pending: '等待中', running: '处理中', paused: '已暂停', cancelled: '已结束', done: '已完成', failed: '失败' }[status] || status
}
function selectVideo(file: UploadFile) { videoFile.value = file.raw || null }
function removeVideo() { videoFile.value = null }
async function runVideo() {
  if (!videoFile.value) return
  loading.value = true; errorText.value = ''; window.clearInterval(timer)
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
    errorText.value = error?.message || '创建失败'
    ElMessage.error(errorText.value)
  } finally { loading.value = false }
}
async function togglePause() {
  if (!task.value) return
  task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause')
  ElMessage.info(task.value.status === 'paused' ? '已暂停' : '已继续')
}
async function endVideo() {
  if (!task.value) return
  try { await ElMessageBox.confirm('确认结束当前视频检测任务？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  task.value = await controlTask(task.value.id, 'cancel')
  window.clearInterval(timer)
  ElMessage.warning('已结束')
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前视频任务？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  task.value = null; errorText.value = ''; window.clearInterval(timer)
  ElMessage.success('已清除')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
