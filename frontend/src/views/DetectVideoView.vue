<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>视频文件检测任务台</h2>
        <p>上传视频创建异步检测任务，实时查看帧流画面、进度与帧级结果。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="task ? 'success' : 'info'">{{ task ? `任务 #${task.id}` : '未创建' }}</el-tag>
      </div>
    </section>

    <!-- 视频检测双栏 -->
    <section class="detection-workbench two-col">
      <!-- 左栏：上传 + 参数 -->
      <DetectionParameterPanel
        :confidence="params.confidence" :iou="params.iou" :save-history="params.save_history"
        :running="running" :can-run="Boolean(videoFile) && !loading" run-label="创建视频任务"
        @run="runVideo"
      >
        <template #extra-params>
          <div class="param-group">
            <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">上传视频文件</label>
            <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
              <p style="font-size:13px;color:var(--color-muted);">选择视频文件</p>
            </el-upload>
          </div>
          <el-progress v-if="task" :percentage="Math.round(task.progress)" :stroke-width="10" style="margin-top:8px;" />
        </template>
        <template #notes>
          <div style="display:flex;gap:8px;margin-top:8px;">
            <el-button size="small" :disabled="!canPause" @click="togglePause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
            <el-button size="small" type="danger" :disabled="!canEnd" @click="endVideo">结束</el-button>
            <el-button size="small" :disabled="!task" @click="clearResults">清除</el-button>
          </div>
        </template>
      </DetectionParameterPanel>

      <!-- 右栏：视频帧流预览 + 任务状态 -->
      <div style="display:grid;gap:var(--gap);">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <span style="font-weight:700;">检测帧流</span>
              <el-tag :type="running ? 'success' : task?.status === 'paused' ? 'warning' : task?.status === 'failed' ? 'danger' : 'info'" size="small">
                {{ task ? statusText(task.status) : '待创建' }}
              </el-tag>
            </div>
          </template>
          <div class="realtime-viewport">
            <img v-if="task" class="video-stream" :src="videoStreamUrl(task.id)" alt="视频检测帧流" style="max-height:500px;" />
            <el-empty v-else description="创建视频任务后显示标注帧流" />
          </div>
          <div class="result-inspector-stats" style="margin-top:12px;">
            <div class="stat-item"><span class="stat-label">采样帧</span><span class="stat-value">{{ summary?.frames_sampled ?? 0 }}</span></div>
            <div class="stat-item"><span class="stat-label">目标数</span><span class="stat-value">{{ summary?.results_count ?? 0 }}</span></div>
            <div class="stat-item"><span class="stat-label">进度</span><span class="stat-value">{{ task ? Math.round(task.progress) : 0 }}%</span></div>
            <div class="stat-item"><span class="stat-label">重试</span><span class="stat-value">{{ task?.retry_count ?? 0 }}/{{ task?.max_retries ?? 3 }}</span></div>
          </div>
        </el-card>

        <DetectionTaskStatus
          v-if="task"
          :status="task.status"
          :progress="Math.round(task.progress)"
          :error="task.error_message"
          :available-actions="[
            { key: 'pause', label: task.status === 'paused' ? '继续' : '暂停', enabled: canPause },
            { key: 'cancel', label: '结束任务', type: 'danger', enabled: canEnd },
          ]"
          @control="(key: string) => key === 'cancel' ? endVideo() : togglePause()"
        />
      </div>
    </section>

    <p v-if="errorText" class="error-text mb">{{ errorText }}</p>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionParameterPanel from '@/components/detection/DetectionParameterPanel.vue'
import DetectionTaskStatus from '@/components/detection/DetectionTaskStatus.vue'
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
  if (!videoFile.value) return; loading.value = true; errorText.value = ''; window.clearInterval(timer)
  try {
    const created = await detectVideo(videoFile.value, { confidence: params.confidence, iou: params.iou, save_history: params.save_history })
    task.value = await getTask(created.task_id); ElMessage.success('视频任务已创建')
    timer = window.setInterval(async () => { if (!task.value) return; task.value = await getTask(task.value.id); if (['done', 'failed', 'cancelled'].includes(task.value.status)) window.clearInterval(timer) }, 1500)
  } catch (error: any) { errorText.value = error?.message || '视频任务创建失败'; ElMessage.error(errorText.value) } finally { loading.value = false }
}
async function togglePause() { if (!task.value) return; task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause'); ElMessage.info(task.value.status === 'paused' ? '已暂停' : '已继续') }
async function endVideo() {
  if (!task.value) return
  try { await ElMessageBox.confirm('确认结束当前视频检测任务？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  task.value = await controlTask(task.value.id, 'cancel'); window.clearInterval(timer); ElMessage.warning('视频检测已结束')
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前视频任务？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  task.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('视频任务已清除')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
