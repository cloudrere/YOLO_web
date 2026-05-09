<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>实时视频流检测</h2>
        <p>连接摄像头、RTSP 或 HTTP 流，实时返回标注画面</p>
      </div>
      <div style="display:flex;gap:8px">
        <el-tag :type="active ? 'success' : 'info'" size="small">{{ active ? '已连接' : '未连接' }}</el-tag>
        <el-tag size="small">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
      </div>
    </div>

    <div class="workbench">
      <div class="workbench-controls">
        <el-card shadow="never">
          <template #header>检测参数</template>
          <label style="font-size:12px;color:#909399">置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
          <label style="font-size:12px;color:#909399">IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="active" />
        </el-card>
        <el-card shadow="never">
          <template #header>实时来源</template>
          <el-input v-model="source" placeholder="摄像头 0 或 RTSP/HTTP 地址" :disabled="active" style="margin-bottom:12px" />
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">
            <el-button type="primary" :disabled="active || !source.trim()" @click="startRealtime">开始</el-button>
            <el-button :disabled="!active && !paused" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button type="danger" :disabled="!active && !paused" @click="stopRealtime">结束</el-button>
          </div>
          <p style="font-size:11px;color:#909399;margin-top:8px">暂停会断开当前 MJPEG 连接，继续时按当前参数重新连接。</p>
          <p v-if="errorText" class="text-danger" style="margin-top:4px;font-size:12px">{{ errorText }}</p>
        </el-card>
      </div>

      <div class="workbench-preview">
        <div class="preview-header">
          <h3>{{ previewTitle }}</h3>
          <el-tag :type="active ? 'success' : paused ? 'warning' : 'info'" size="small">{{ statusText }}</el-tag>
        </div>
        <div class="preview-canvas">
          <img v-if="streamUrl" :src="streamUrl" alt="实时视频流检测" style="max-width:100%;max-height:100%;object-fit:contain" />
          <el-empty v-else :description="paused ? '流已暂停，继续后重新连接' : '连接实时流后显示标注画面'" :image-size="48" />
        </div>
        <div class="preview-stats">
          <div><strong>{{ elapsed }}</strong><span>运行秒数</span></div>
          <div><strong>{{ source || '0' }}</strong><span>来源</span></div>
          <div><strong>{{ active ? 'ON' : 'OFF' }}</strong><span>连接状态</span></div>
        </div>
      </div>
    </div>

    <el-card shadow="never">
      <template #header><div class="flex-between"><span>状态面板</span><el-button size="small" :disabled="!active && !paused" @click="stopRealtime">清除结果</el-button></div></template>
      <p style="font-size:13px">{{ statusText }}；来源：{{ source || '0' }}；运行时长：{{ elapsed }} 秒；协议：MJPEG。</p>
    </el-card>
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
const statusText = computed(() => (active.value ? '实时检测正在运行' : paused.value ? '实时检测已暂停' : '实时检测未连接'))

function startRealtime() {
  streamUrl.value = realtimeStreamUrl(source.value, { confidence: params.confidence, iou: params.iou })
  active.value = true; paused.value = false; startedAt.value = Date.now(); errorText.value = ''
  ElMessage.success('实时流已连接')
  window.clearInterval(timer)
  timer = window.setInterval(() => { tick.value += 1 }, 1000)
}
function togglePause() {
  if (streamUrl.value) { streamUrl.value = ''; active.value = false; paused.value = true; window.clearInterval(timer); ElMessage.info('实时流已暂停'); return }
  startRealtime()
}
async function stopRealtime() {
  try { await ElMessageBox.confirm('确认结束当前实时流连接吗？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  streamUrl.value = ''; active.value = false; paused.value = false; startedAt.value = null; errorText.value = ''; window.clearInterval(timer); ElMessage.success('实时流已结束')
}
onBeforeUnmount(() => window.clearInterval(timer))
</script>
