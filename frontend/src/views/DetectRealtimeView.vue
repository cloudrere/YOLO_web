<template>
  <AppLayout>
    <!-- 顶部状态条 -->
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow">实时监控</span>
        <h2>摄像头与流媒体在线推理</h2>
        <p>连接本机摄像头、RTSP 或 HTTP(S) 流，实时返回 YOLO 标注画面。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="active ? 'success' : 'info'">{{ active ? '● 已连接' : '○ 未连接' }}</el-tag>
        <el-tag>{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </section>

    <!-- 三栏核心区域：左侧源 → 中间画面 → 右侧状态 -->
    <section class="grid three" style="align-items: stretch; margin-bottom: var(--gap);">
      <!-- 左侧：源配置 -->
      <el-card shadow="never" class="panel-card detection-control-rail">
        <template #header>信号源配置</template>
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="mode-config">
          <h3>视频源地址</h3>
          <el-input v-model="source" size="large" placeholder="摄像头 0 或 RTSP/HTTP 地址" :disabled="active" />
          <div class="split-actions three-actions">
            <el-button type="primary" size="large" :disabled="active || !source.trim()" @click="startRealtime">开始</el-button>
            <el-button size="large" :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button size="large" type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
          </div>
          <p class="control-note">暂停会断开当前 MJPEG 连接，继续时按当前参数重新连接。</p>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </el-card>

      <!-- 中间：大画面 -->
      <el-card shadow="never" class="panel-card detection-preview-stage" style="grid-column: span 1;">
        <template #header>
          <div class="preview-header" style="margin-bottom: 0;">
            <div><span>实时监控画面</span><strong>{{ active ? '● 在线' : paused ? '⏸ 已暂停' : '○ 离线' }}</strong></div>
            <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'">{{ active ? '推流中' : paused ? '已暂停' : '待连接' }}</el-tag>
          </div>
        </template>
        <div class="preview-canvas">
          <img v-if="streamUrl" class="video-stream" :src="streamUrl" alt="实时视频流检测" style="margin-top: 0; max-height: none;" />
          <el-empty v-else :description="paused ? '流已暂停，继续后重新连接' : '连接实时流后显示标注画面'" />
        </div>
      </el-card>

      <!-- 右侧：实时状态 -->
      <el-card shadow="never" class="panel-card">
        <template #header>连接状态</template>
        <div class="realtime-guide" style="margin-bottom: 16px;">
          <strong :style="{ color: active ? 'var(--status-online)' : paused ? 'var(--status-warning)' : 'var(--text-muted)' }">{{ active ? '● 实时检测运行中' : paused ? '⏸ 实时检测已暂停' : '○ 实时检测未连接' }}</strong>
          <p>来源：{{ source || '0' }}；运行时长：{{ elapsed }} 秒；协议：MJPEG。</p>
        </div>
        <div class="preview-metrics" style="grid-template-columns: 1fr;">
          <div><strong>{{ elapsed }}</strong><span>运行秒数</span></div>
          <div><strong>{{ source || '0' }}</strong><span>信号来源</span></div>
          <div><strong>{{ active ? 'ONLINE' : 'OFFLINE' }}</strong><span>连接状态</span></div>
        </div>
      </el-card>
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

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true
  paused.value = false
  startedAt.value = Date.now()
  errorText.value = ''
  ElMessage.success('实时流已连接')
  window.clearInterval(timer)
  timer = window.setInterval(() => { tick.value += 1 }, 1000)
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
