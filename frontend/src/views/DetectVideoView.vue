<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>视频文件检测</h2>
        <p>上传视频创建异步抽帧检测任务</p>
      </div>
      <div style="display:flex;gap:8px">
        <el-tag :type="task ? 'success' : 'info'" size="small">{{ task ? `任务 ${task.id}` : '未创建' }}</el-tag>
        <el-tag size="small">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </div>

    <div class="workbench">
      <div class="workbench-controls">
        <el-card shadow="never">
          <template #header>检测参数</template>
          <label style="font-size:12px;color:#909399">置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <label style="font-size:12px;color:#909399">IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="running" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="running" style="margin-top:8px" />
        </el-card>
        <el-card shadow="never">
          <template #header>上传视频</template>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectVideo" :on-remove="removeVideo" :disabled="running">
            <p>选择视频文件后创建检测任务</p>
          </el-upload>
          <div class="progress-wrap"><el-progress v-if="task" :percentage="Math.round(task.progress)" :stroke-width="10" /></div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:12px">
            <el-button type="primary" :disabled="!videoFile || loading || running" :loading="loading" @click="runVideo">开始</el-button>
            <el-button :disabled="!canPause" @click="togglePause">{{ task?.status === 'paused' ? '继续' : '暂停' }}</el-button>
            <el-button type="danger" :disabled="!canEnd" @click="endVideo">结束</el-button>
          </div>
          <p v-if="errorText" class="text-danger" style="margin-top:8px;font-size:12px">{{ errorText }}</p>
        </el-card>
      </div>

      <div class="workbench-preview">
        <div class="preview-header">
          <h3>{{ task ? statusText(task.status) : '等待视频任务' }}</h3>
          <el-tag :type="running ? 'success' : task?.status === 'paused' ? 'warning' : task?.status === 'failed' ? 'danger' : 'info'" size="small">{{ task ? statusText(task.status) : '待创建' }}</el-tag>
        </div>
        <div class="preview-canvas">
          <img v-if="task" :src="videoStreamUrl(task.id)" alt="视频检测标注流" style="max-width:100%;max-height:100%;object-fit:contain" />
          <el-empty v-else description="创建视频任务后显示标注帧流" :image-size="48" />
        </div>
        <div class="preview-stats">
          <div><strong>{{ summary?.frames_sampled ?? 0 }}</strong><span>采样帧</span></div>
          <div><strong>{{ summary?.results_count ?? 0 }}</strong><span>目标数</span></div>
          <div><strong>{{ task ? `${Math.round(task.progress)}%` : '0%' }}</strong><span>进度</span></div>
        </div>
      </div>
    </div>

    <el-card v-if="task" shadow="never">
      <template #header><div class="flex-between"><span>任务状态</span><el-button size="small" @click="clearResults">清除结果</el-button></div></template>
      <div class="progress-wrap"><el-progress :percentage="Math.round(task.progress)" :stroke-width="12" /></div>
      <div style="display:flex;gap:24px;font-size:13px;color:#909399;margin-top:8px">
        <span>状态：{{ statusText(task.status) }}</span>
        <span>重试：{{ task.retry_count }}/{{ task.max_retries }}</span>
        <span>任务 ID：{{ task.id }}</span>
      </div>
      <p v-if="task.error_message" class="text-danger" style="margin-top:8px;font-size:12px">{{ task.error_message }}</p>
    </el-card>
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
    const created = await detectVideo(videoFile.value, { ...params })
    task.value = await getTask(created.task_id); ElMessage.success('视频检测任务已创建')
    timer = window.setInterval(async () => { if (!task.value) return; task.value = await getTask(task.value.id); if (['done', 'failed', 'cancelled'].includes(task.value.status)) window.clearInterval(timer) }, 1500)
  } catch (error: any) { errorText.value = error?.message || '视频检测任务创建失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false }
}
async function togglePause() { if (!task.value) return; task.value = await controlTask(task.value.id, task.value.status === 'paused' ? 'resume' : 'pause'); ElMessage.info(task.value.status === 'paused' ? '视频任务已暂停' : '视频任务已继续') }
async function endVideo() { if (!task.value) return; try { await ElMessageBox.confirm('确认结束当前视频检测任务吗？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }; task.value = await controlTask(task.value.id, 'cancel'); window.clearInterval(timer); ElMessage.warning('视频检测已结束') }
async function clearResults() { try { await ElMessageBox.confirm('确认清除当前视频任务和结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }; task.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('结果已清除') }
onBeforeUnmount(() => window.clearInterval(timer))
</script>
