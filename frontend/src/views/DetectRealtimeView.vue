<template>
  <AppLayout>
    <section class="detection-status-strip">
      <div>
        <span class="eyebrow dark">实时流监控工作区</span>
        <h2>摄像头与流媒体在线推理</h2>
        <p>连接摄像头、RTSP 或 HTTP(S) 流，实时显示 YOLO 标注画面，支持暂停断开和重新连接。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="active ? 'success' : 'info'">{{ active ? '已连接' : '未连接' }}</el-tag>
        <el-tag>置信度 {{ params.confidence.toFixed(2) }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench two-col">
      <!-- 左侧：连接配置 -->
      <aside class="detection-control-rail workstation-panel">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度 {{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
          <label>IoU 阈值 {{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div style="padding: 16px; border-top: 1px solid var(--border-soft);">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: var(--color-primary-deep);">流媒体源</h3>
          <el-input v-model="source" size="large" placeholder="摄像头编号 0 或 RTSP/HTTP 地址" :disabled="active" />
          <div class="split-actions three-actions" style="margin-top: 14px;">
            <el-button type="primary" size="small" :disabled="active || !source.trim()" @click="startRealtime">连接</el-button>
            <el-button size="small" :disabled="!active && !paused" @click="togglePause">{{ paused ? '重连' : '暂停' }}</el-button>
            <el-button size="small" type="danger" :disabled="!active && !paused" @click="stopRealtime">断开</el-button>
          </div>
          <p class="control-note">暂停会断开 MJPEG 连接，重连时使用当前参数。</p>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>

        <!-- 连接统计 -->
        <div style="margin-top: 16px; padding: 16px; border: 1px solid var(--border-soft); border-radius: 12px; background: var(--color-surface-alt);">
          <h3 style="margin: 0 0 12px; font-size: 14px; color: var(--color-primary-deep);">连接信息</h3>
          <div style="display: grid; gap: 8px;">
            <div style="display: flex; justify-content: space-between;"><span style="color: var(--color-muted); font-size: 12px;">来源</span><strong style="color: var(--color-primary-deep); font-size: 13px;">{{ source || '0' }}</strong></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: var(--color-muted); font-size: 12px;">运行时长</span><strong style="color: var(--color-primary-deep); font-size: 13px;">{{ elapsed }} 秒</strong></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: var(--color-muted); font-size: 12px;">协议</span><strong style="color: var(--color-primary-deep); font-size: 13px;">MJPEG</strong></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: var(--color-muted); font-size: 12px;">状态</span><el-tag :type="active ? 'success' : 'info'" size="small">{{ active ? 'ON' : 'OFF' }}</el-tag></div>
          </div>
        </div>
      </aside>

      <!-- 右侧：实时画面最大化 -->
      <main class="detection-preview-stage workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">实时画面</span><strong style="display: block; font-size: 20px; margin-top: 2px; color: var(--color-primary-deep);">{{ previewTitle }}</strong></div>
          <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'" size="small">{{ statusText }}</el-tag>
        </div>
        <div class="preview-canvas" style="background: #1a202c; min-height: clamp(420px, 55vw, 680px);">
          <img v-if="streamUrl" class="video-stream" :src="streamUrl" alt="实时视频流检测" style="max-height: 660px;" />
          <el-empty v-else :description="paused ? '流已暂停，点击重连' : '连接实时流后显示标注画面'" />
        </div>
      </main>
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

const elapsed = computed(() => { tick.value; return startedAt.value ? Math.floor((Date.now() - startedAt.value) / 1000) : 0 })
const previewTitle = computed(() => (active.value ? '实时检测中' : paused.value ? '已暂停' : '未连接'))
const statusText = computed(() => (active.value ? '实时检测运行中' : paused.value ? '已暂停' : '未连接'))

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true; paused.value = false; startedAt.value = Date.now(); errorText.value = ''
  ElMessage.success('实时流已连接')
  window.clearInterval(timer)
  timer = window.setInterval(() => { tick.value += 1 }, 1000)
}
function togglePause() {
  if (streamUrl.value) {
    streamUrl.value = ''; active.value = false; paused.value = true; window.clearInterval(timer)
    ElMessage.info('实时流已暂停')
    return
  }
  startRealtime()
}
async function stopRealtime() {
  try { await ElMessageBox.confirm('确认断开实时流连接？', '断开确认', { type: 'warning', confirmButtonText: '确认断开', cancelButtonText: '取消' }) } catch { return }
  streamUrl.value = ''; active.value = false; paused.value = false; startedAt.value = null; errorText.value = ''
  window.clearInterval(timer)
  ElMessage.success('已断开')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<style scoped>
@media (max-width: 768px) {
  .detection-workbench.two-col { grid-template-columns: 1fr; }
}
</style>
