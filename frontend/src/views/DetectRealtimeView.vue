<template>
  <AppLayout>
    <!-- Hero 横幅 -->
    <section class="workstation-hero flex-between">
      <div class="flex-wrap" style="gap:14px;">
        <span class="pulse-dot" :class="active ? 'running' : paused ? 'warning' : 'idle'" style="width:14px;height:14px;" :title="active ? '运行中' : paused ? '已暂停' : '未连接'" />
        <div>
          <span class="eyebrow dark">实时视频流检测</span>
          <h2>摄像头与流媒体在线推理</h2>
          <p>连接本机摄像头、RTSP 或 HTTP(S) 流，实时返回标注画面，暂停会断开连接。</p>
        </div>
      </div>
      <div class="status-pills">
        <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'" size="large">{{ active ? '已连接' : paused ? '已暂停' : '未连接' }}</el-tag>
        <el-tag>{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <!-- 三栏检测工作台 -->
    <section class="detection-workbench">
      <!-- 左栏：连接配置 -->
      <aside class="panel-card">
        <h3 class="panel-title" style="font-size:16px;">实时来源</h3>
        <el-input
          v-model="source"
          size="large"
          placeholder="摄像头 0 或 RTSP/HTTP 地址"
          :disabled="active"
        />
        <h3 class="panel-title" style="font-size:16px;margin-top:20px;">检测参数</h3>
        <div class="param-row">
          <label>置信度阈值 <span class="param-value">{{ params.confidence.toFixed(2) }}</span></label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="param-row">
          <label>IoU 阈值 <span class="param-value">{{ params.iou.toFixed(2) }}</span></label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="split-actions three-col">
          <el-button type="primary" size="large" :disabled="active || !source.trim()" @click="startRealtime">开始</el-button>
          <el-button size="large" :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button size="large" type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
        </div>
        <p v-if="errorText" class="error-text" style="margin-top:12px;">{{ errorText }}</p>
      </aside>

      <!-- 中栏：实时视口 -->
      <main class="realtime-viewport">
        <div class="panel-card" style="padding:16px 20px;">
          <div class="flex-between">
            <div>
              <span class="metric-label">{{ previewTitle }}</span>
            </div>
            <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'" size="large">{{ statusText }}</el-tag>
          </div>
        </div>
        <div class="detect-canvas" :class="{ 'has-image': active && streamUrl }" style="min-height:460px;">
          <img v-if="active && streamUrl" class="video-stream" :src="streamUrl" alt="实时视频流检测" style="max-height:520px;width:100%;" />
          <div v-else class="empty-detect-canvas">
            <div class="scan-overlay"><div class="scan-line" /></div>
            <div class="placeholder-content">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none" style="opacity:0.25;">
                <rect x="8" y="8" width="48" height="48" rx="4" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4" />
                <rect x="20" y="20" width="24" height="16" rx="2" stroke="currentColor" stroke-width="1.5" />
                <circle cx="32" cy="28" r="4" stroke="currentColor" stroke-width="1.5" />
              </svg>
              <strong>{{ paused ? '流已暂停' : '未连接实时流' }}</strong>
              <span>{{ paused ? '按"继续"重新连接当前来源' : '填入来源地址后点击"开始"连接检测' }}</span>
            </div>
          </div>
          <div v-if="active" class="scan-overlay"><div class="scan-line" /></div>
        </div>
        <div class="grid three">
          <div class="metric-card">
            <span class="metric-label">连接状态</span>
            <span class="metric-value" style="font-size:22px;">{{ active ? 'ON' : 'OFF' }}</span>
            <span class="metric-desc">{{ active ? 'MJPEG 流传输中' : '未建立连接' }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">检测来源</span>
            <span class="metric-value" style="font-size:22px;">{{ source || '0' }}</span>
            <span class="metric-desc">{{ source === '0' ? '本机摄像头' : '外部流地址' }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">运行秒数</span>
            <span class="metric-value" style="font-size:22px;">{{ elapsed }}</span>
            <span class="metric-desc">实时累计运行时长</span>
          </div>
        </div>
      </main>

      <!-- 右栏：实时状态 + 提示 -->
      <div class="realtime-side">
        <div class="panel-card">
          <h3 class="panel-title" style="font-size:16px;margin-bottom:16px;">连接详情</h3>
          <div class="health-status-line">
            <span>连接状态</span>
            <strong :style="{ color: active ? 'var(--status-success)' : paused ? 'var(--status-warning)' : 'var(--color-soft)' }">{{ statusText }}</strong>
          </div>
          <div class="health-status-line">
            <span>来源</span><strong>{{ source || '0' }}</strong>
          </div>
          <div class="health-status-line">
            <span>运行时长</span><strong>{{ elapsed }} 秒</strong>
          </div>
          <div class="health-status-line">
            <span>传输协议</span><strong>MJPEG</strong>
          </div>
          <div class="health-status-line">
            <span>置信度</span><strong>{{ params.confidence.toFixed(2) }}</strong>
          </div>
          <div class="health-status-line">
            <span>IoU 阈值</span><strong>{{ params.iou.toFixed(2) }}</strong>
          </div>
        </div>
        <div class="realtime-tip">
          <p>
            <strong>操作说明</strong>
            暂停会断开当前 MJPEG 连接；<br />继续时按当前参数重新连接；<br />结束检测后需重新点击开始。
          </p>
        </div>
      </div>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { realtimeStreamUrl } from '@/api/detect'

const source = ref('0')
const streamUrl = ref('')
const active = ref(false)
const paused = ref(false)
const startedAt = ref<number | null>(null)
const tick = ref(0)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7 })
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
