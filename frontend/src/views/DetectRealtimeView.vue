<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>实时流检测工作台</h2>
        <p>接入摄像头、RTSP 或 HTTP(S) 推流，实时返回 YOLO 标注画面。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="active ? 'success' : 'info'">{{ active ? '已连接' : '未连接' }}</el-tag>
      </div>
    </section>

    <!-- 实时流检测三栏：配置 → 画面 → 状态 -->
    <section class="detection-workbench">
      <!-- 左栏：连接配置 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">连接配置</span></template>
        <div class="param-group">
          <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">流来源地址</label>
          <el-input v-model="source" size="large" placeholder="摄像头 0 或 RTSP/HTTP 地址" :disabled="active" />
        </div>
        <div class="param-group">
          <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <div class="param-group">
          <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">IoU：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </div>
        <el-button type="primary" class="full" :disabled="active || !source.trim()" @click="startRealtime">开始连接</el-button>
        <div style="display:flex;gap:8px;margin-top:8px;">
          <el-button class="full" size="small" :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button class="full" size="small" type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
        </div>
        <p v-if="errorText" class="error-text" style="margin-top:8px;">{{ errorText }}</p>
      </el-card>

      <!-- 中栏：实时画面（视觉中心） -->
      <el-card shadow="never">
        <template #header>
          <div class="flex-between">
            <span style="font-weight:700;">实时检测画面</span>
            <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'" size="small">
              {{ active ? 'LIVE' : paused ? 'PAUSED' : 'IDLE' }}
            </el-tag>
          </div>
        </template>
        <div class="realtime-viewport" style="min-height:520px;">
          <img v-if="streamUrl" class="video-stream" :src="streamUrl" alt="实时检测流" style="max-height:580px;" />
          <el-empty v-else :description="paused ? '已暂停 — 点击继续重新连接' : '配置来源并点击开始连接'" />
        </div>
      </el-card>

      <!-- 右栏：实时统计 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">实时状态监控</span></template>
        <div class="result-inspector-stats" style="grid-template-columns:1fr;">
          <div class="stat-item"><span class="stat-label">连接状态</span><span class="stat-value" style="font-size:16px;">{{ active ? '已连接' : paused ? '已暂停' : '未连接' }}</span></div>
          <div class="stat-item"><span class="stat-label">流来源</span><span class="stat-value" style="font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ source || '0' }}</span></div>
          <div class="stat-item"><span class="stat-label">运行时长</span><span class="stat-value">{{ elapsed }}s</span></div>
          <div class="stat-item"><span class="stat-label">传输协议</span><span class="stat-value" style="font-size:14px;">MJPEG</span></div>
          <div class="stat-item"><span class="stat-label">置信度</span><span class="stat-value" style="font-size:14px;">{{ params.confidence.toFixed(2) }}</span></div>
          <div class="stat-item"><span class="stat-label">IoU</span><span class="stat-value" style="font-size:14px;">{{ params.iou.toFixed(2) }}</span></div>
        </div>
        <div style="margin-top:12px;padding:12px;border-radius:var(--radius-sm);background:#eff6ff;border:1px solid #bfdbfe;">
          <span style="font-size:12px;color:var(--color-muted);">暂停会断开 MJPEG 连接。继续时按当前参数重新连接。</span>
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

const elapsed = computed(() => { tick.value; return startedAt.value ? Math.floor((Date.now() - startedAt.value) / 1000) : 0 })

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true; paused.value = false; startedAt.value = Date.now(); errorText.value = ''; ElMessage.success('实时流已连接')
  window.clearInterval(timer); timer = window.setInterval(() => { tick.value += 1 }, 1000)
}
function togglePause() {
  if (streamUrl.value) { streamUrl.value = ''; active.value = false; paused.value = true; window.clearInterval(timer); ElMessage.info('已暂停'); return }
  startRealtime()
}
async function stopRealtime() {
  try { await ElMessageBox.confirm('确认结束当前实时流连接？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  streamUrl.value = ''; active.value = false; paused.value = false; startedAt.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('实时流已结束')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
