<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>视频分析台</h1>
        <p>上传视频创建异步任务，实时帧流、任务进度和检测元信息。</p>
      </div>
      <div class="ws-tags">
        <el-tag size="small" :type="task ? 'success' : 'info'">{{ task ? `任务 #${task.id}` : '未创建任务' }}</el-tag>
        <el-tag size="small">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </div>

    <div class="ws-panel-2">
      <div class="ws-tool-panel">
        <div class="panel-label">检测参数</div>
        <div class="ws-param-group">
          <label>置信度 <span>{{ params.confidence.toFixed(2) }}</span></label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
        </div>
        <div class="ws-param-group">
          <label>IoU 阈值 <span>{{ params.iou.toFixed(2) }}</span></label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
        </div>
        <div class="ws-param-group">
          <el-switch v-model="params.save_history" active-text="保存历史" inactive-text="仅本地" :disabled="running" />
        </div>
        <div class="ws-tool-divider"></div>
        <div class="panel-label">视频源</div>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
          <p>选择视频文件</p>
        </el-upload>
        <el-progress v-if="task" :percentage="Math.round(task.progress)" :stroke-width="6" class="ws-progress" />
        <div class="flex-gap" style="margin-top:8px">
          <el-button type="primary" :disabled="!videoFile || loading || running" :loading="loading" @click="runVideo">开始</el-button>
          <el-button :disabled="!canPause" @click="togglePause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
          <el-button type="danger" :disabled="!canEnd" @click="endVideo">结束</el-button>
        </div>
        <p v-if="errorText" class="text-danger" style="margin-top:8px">{{ errorText }}</p>
      </div>

      <div>
        <div class="ws-preview-stage" style="margin-bottom:10px">
          <div class="ws-preview-header">
            <span>{{ task ? statusText(task.status) : '等待视频任务' }}</span>
            <el-tag size="small" :type="running ? 'success' : task?.status === 'paused' ? 'warning' : task?.status === 'failed' ? 'danger' : 'info'">{{ task ? statusText(task.status) : 'IDLE' }}</el-tag>
          </div>
          <div class="ws-preview-canvas">
            <img v-if="task" class="video-stream" :src="videoStreamUrl(task.id)" alt="视频标注流" />
            <span v-else style="color:var(--text-muted);font-size:13px">创建任务后显示标注帧流</span>
          </div>
          <div class="ws-preview-footer">
            <div class="foot-stat"><span class="stat-num">{{ summary?.frames_sampled ?? 0 }}</span><span class="stat-label">采样帧</span></div>
            <div class="foot-stat"><span class="stat-num">{{ summary?.results_count ?? 0 }}</span><span class="stat-label">目标数</span></div>
            <div class="foot-stat"><span class="stat-num">{{ task ? Math.round(task.progress) + '%' : '0%' }}</span><span class="stat-label">进度</span></div>
          </div>
        </div>

        <div v-if="task" class="ws-card">
          <div class="ws-card-header">
            <span>任务详情</span>
            <el-button size="small" @click="clearResults">清除</el-button>
          </div>
          <div class="ws-card-body">
            <el-progress :percentage="Math.round(task.progress)" :stroke-width="10" style="margin-bottom:10px" />
            <div class="ws-info-grid">
              <div class="ws-info-item"><span class="info-label">状态</span><span class="info-value">{{ statusText(task.status) }}</span></div>
              <div class="ws-info-item"><span class="info-label">重试</span><span class="info-value">{{ task.retry_count }}/{{ task.max_retries }}</span></div>
              <div class="ws-info-item"><span class="info-label">任务 ID</span><span class="info-value">{{ task.id }}</span></div>
            </div>
            <p v-if="task.error_message" class="text-danger" style="margin-top:8px">{{ task.error_message }}</p>
          </div>
        </div>
      </div>
    </div>
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
const summary = computed<VideoSummary | null>(() => { if (!task.value?.result_json) return null; try { return JSON.parse(task.value.result_json) as VideoSummary } catch { return null } })

function statusText(status: string) { return { pending: '等待中', running: '处理中', paused: '已暂停', cancelled: '已结束', done: '已完成', failed: '失败' }[status] || status }
function selectVideo(file: UploadFile) { videoFile.value = file.raw || null }
function removeVideo() { videoFile.value = null }
async function runVideo() {
  if (!videoFile.value) return
  loading.value = true; errorText.value = ''; window.clearInterval(timer)
  try {
    const created = await detectVideo(videoFile.value, { ...params }); task.value = await getTask(created.task_id)
    ElMessage.success('视频检测任务已创建')
    timer = window.setInterval(async () => { if (!task.value) return; task.value = await getTask(task.value.id); if (['done', 'failed', 'cancelled'].includes(task.value.status)) window.clearInterval(timer) }, 1500)
  } catch (error: any) { errorText.value = error?.message || '视频检测任务创建失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false }
}
async function togglePause() { if (!task.value) return; task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause'); ElMessage.info(task.value.status === 'paused' ? '视频任务已暂停' : '视频任务已继续') }
async function endVideo() { if (!task.value) return; try { await ElMessageBox.confirm('确认结束当前视频检测任务吗？', '结束确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; task.value = await controlTask(task.value.id, 'cancel'); window.clearInterval(timer); ElMessage.warning('视频检测已结束') }
async function clearResults() { try { await ElMessageBox.confirm('确认清除当前视频任务和结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; task.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('结果已清除') }
onBeforeUnmount(() => window.clearInterval(timer))
</script>
