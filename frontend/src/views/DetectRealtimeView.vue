<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>实时视觉流工作区</h1>
        <p>连接摄像头或 RTSP/HTTP 流，实时 YOLO 标注 MJPEG 输出。</p>
      </div>
      <div class="ws-tags">
        <el-tag size="small" :type="active ? 'success' : 'info'">{{ active ? 'LIVE' : '未连接' }}</el-tag>
        <el-tag size="small">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </div>

    <div class="ws-panel-2">
      <!-- 控制面板 -->
      <div class="ws-tool-panel">
        <div class="panel-label">检测参数</div>
        <div class="ws-param-group">
          <label>置信度 <span>{{ params.confidence.toFixed(2) }}</span></label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="ws-param-group">
          <label>IoU 阈值 <span>{{ params.iou.toFixed(2) }}</span></label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="ws-tool-divider"></div>
        <div class="panel-label">流来源</div>
        <el-input v-model="source" placeholder="摄像头 0 或 RTSP/HTTP 地址" :disabled="active" class="mb" />
        <div class="flex-gap">
          <el-button type="primary" :disabled="active || !source.trim()" @click="startRealtime">开始</el-button>
          <el-button :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
        </div>
        <p style="margin-top:8px;font-size:10px;color:var(--text-muted)">暂停会断开 MJPEG 连接，继续时重新连接。</p>
        <p v-if="errorText" class="text-danger" style="margin-top:8px">{{ errorText }}</p>
      </div>

      <!-- 实时画面 -->
      <div>
        <div class="ws-preview-stage" style="margin-bottom:10px">
          <div class="ws-preview-header">
            <span>{{ previewTitle }}</span>
            <el-tag size="small" :type="active ? 'success' : paused ? 'warning' : 'info'">{{ active ? 'LIVE' : paused ? 'PAUSED' : 'IDLE' }}</el-tag>
          </div>
          <div class="ws-preview-canvas">
            <img v-if="streamUrl" class="video-stream" :src="streamUrl" alt="实时流" />
            <span v-else style="color:var(--text-muted);font-size:13px">{{ paused ? '流已暂停' : '连接实时流后显示标注画面' }}</span>
          </div>
          <div class="ws-preview-footer">
            <div class="foot-stat"><span class="stat-num">{{ elapsed }}</span><span class="stat-label">运行秒数</span></div>
            <div class="foot-stat"><span class="stat-num">{{ source || '0' }}</span><span class="stat-label">来源</span></div>
            <div class="foot-stat"><span class="stat-num" :style="{color: active ? 'var(--success)' : 'var(--text-muted)'}">{{ active ? 'ON' : 'OFF' }}</span><span class="stat-label">连接状态</span></div>
          </div>
        </div>

        <div class="ws-card">
          <div class="ws-card-header">
            <span>实时状态面板</span>
            <el-button size="small" :disabled="!active && !paused" @click="stopRealtime">清除</el-button>
          </div>
          <div class="ws-card-body">
            <div class="ws-info-grid">
              <div class="ws-info-item"><span class="info-label">状态</span><span class="info-value">{{ statusText }}</span></div>
              <div class="ws-info-item"><span class="info-label">来源</span><span class="info-value">{{ source || '0' }}</span></div>
              <div class="ws-info-item"><span class="info-label">运行时长</span><span class="info-value">{{ elapsed }} 秒</span></div>
              <div class="ws-info-item"><span class="info-label">协议</span><span class="info-value">MJPEG</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
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
const statusText = computed(() => (active.value ? '实时检测运行中' : paused.value ? '实时检测已暂停' : '未连接'))

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true; paused.value = false; startedAt.value = Date.now(); errorText.value = ''
  ElMessage.success('实时流已连接'); window.clearInterval(timer); timer = window.setInterval(() => { tick.value += 1 }, 1000)
}
function togglePause() {
  if (streamUrl.value) { streamUrl.value = ''; active.value = false; paused.value = true; window.clearInterval(timer); ElMessage.info('实时流已暂停'); return }
  startRealtime()
}
async function stopRealtime() {
  try { await ElMessageBox.confirm('确认结束当前实时流连接吗？', '结束确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }
  streamUrl.value = ''; active.value = false; paused.value = false; startedAt.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('实时流已结束')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
