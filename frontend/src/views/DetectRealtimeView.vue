<template>
  <AppLayout>
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow dark">实时视频流检测</span>
        <h2>摄像头与流媒体在线推理</h2>
        <p>连接本机摄像头、RTSP 或 HTTP(S) 流，实时返回标注画面，暂停会断开连接。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="active ? 'success' : 'info'">{{ active ? '已连接' : '未连接' }}</el-tag>
        <el-tag type="info">实时流不生成 AI 分析</el-tag>
        <el-tag>{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench single-flow">
      <aside class="detection-control-rail panel-card">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="mode-config">
          <h3>实时来源</h3>
          <el-input v-model="source" size="large" placeholder="摄像头 0 或 RTSP/HTTP 地址" :disabled="active" />
          <div class="split-actions three-actions">
            <el-button type="primary" size="large" :disabled="active || !source.trim()" @click="startRealtime">开始</el-button>
            <el-button size="large" :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button size="large" type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
          </div>
          <p class="control-note">暂停会断开当前 MJPEG 连接，继续时按当前参数重新连接。</p>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <main class="detection-preview-stage panel-card">
        <div class="preview-header">
          <div><span>实时画面</span><strong>{{ previewTitle }}</strong></div>
          <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'">{{ statusText }}</el-tag>
        </div>
        <div class="preview-canvas">
          <img v-if="streamUrl" class="video-stream" :src="streamUrl" alt="实时视频流检测" />
          <el-empty v-else :description="paused ? '流已暂停，继续后重新连接' : '连接实时流后显示标注画面'" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ elapsed }}</strong><span>运行秒数</span></div>
          <div><strong>{{ source || '0' }}</strong><span>来源</span></div>
          <div><strong>{{ active ? 'ON' : 'OFF' }}</strong><span>连接状态</span></div>
        </div>
      </main>
    </section>

    <section class="detection-inspector panel-card">
      <div class="inspector-header">
        <div><span class="eyebrow dark">实时状态面板</span><h3>连接与帧率信息</h3></div>
        <el-button :disabled="!active && !paused" @click="stopRealtime">清除结果</el-button>
      </div>
      <div class="realtime-guide">
        <strong>{{ statusText }}</strong>
        <p>来源：{{ source || '0' }}；运行时长：{{ elapsed }} 秒；协议：MJPEG。</p>
      </div>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { realtimeStreamUrl, type DetectParameters } from '@/api/detect'

const source = ref('0')
const streamUrl = ref('')
const active = ref(false)
const paused = ref(false)
const startedAt = ref<number | null>(null)
const tick = ref(0)
const errorText = ref('')
const params = reactive<Required<DetectParameters>>({ confidence: 0.25, iou: 0.7, save_history: false, analyze: false })
let timer: number | undefined

const elapsed = computed(() => {
  tick.value
  return startedAt.value ? Math.floor((Date.now() - startedAt.value) / 1000) : 0
})
const previewTitle = computed(() => (active.value ? '实时检测中' : paused.value ? '已暂停' : '未连接'))
const statusText = computed(() => (active.value ? '实时检测正在运行' : paused.value ? '实时检测已暂停' : '实时检测未连接'))

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true
  paused.value = false
  startedAt.value = Date.now()
  errorText.value = ''
  ElMessage.success('实时流已连接')
  window.clearInterval(timer)
  timer = window.setInterval(() => {
    tick.value += 1
  }, 1000)
}
function togglePause() {
  if (streamUrl.value) {
    streamUrl.value = ''
    active.value = false
    paused.value = true
    window.clearInterval(timer)
    ElMessage.info('实时流已暂停')
    return
  }
  startRealtime()
}
async function stopRealtime() {
  try {
    await ElMessageBox.confirm('确认结束当前实时流连接吗？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' })
  } catch {
    return
  }
  streamUrl.value = ''
  active.value = false
  paused.value = false
  startedAt.value = null
  errorText.value = ''
  window.clearInterval(timer)
  ElMessage.success('实时流已结束')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
