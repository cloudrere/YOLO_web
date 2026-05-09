<template>
  <AppLayout>
    <!-- Hero: 检测模式选择标题 + 模型状态条 -->
    <section class="workstation-hero">
      <div>
        <h2>选择检测模式</h2>
        <p>四种独立检测工作流 — 单图、批量、视频文件或实时推流，参数与结果互不串扰。</p>
      </div>
      <ModelStatusBar ref="modelBarRef" />
    </section>

    <!-- 四张模式入口卡 -->
    <section class="detect-mode-grid" style="margin-bottom:var(--gap);">
      <DetectionModeCard
        v-for="mode in modes" :key="mode.path"
        :to="mode.path" :icon="mode.icon" :title="mode.title"
        :desc="mode.description" :action="mode.action"
      />
    </section>

    <!-- 最近检测 + 系统准备状态 -->
    <el-card shadow="never">
      <template #header><span style="font-weight:700;">系统准备状态</span></template>
      <div class="grid two">
        <div>
          <div class="health-status-line"><span>当前模型</span><strong>{{ modelDisplayName }}</strong></div>
          <div class="health-status-line"><span>推理设备</span><strong>{{ deviceLabel }}</strong></div>
          <div class="health-status-line"><span>预热状态</span><el-tag :type="warmupTagType" size="small">{{ warmupText }}</el-tag></div>
        </div>
        <div>
          <div class="health-status-line"><span>CUDA</span><el-tag :type="modelState?.cuda_available ? 'success' : 'info'" size="small">{{ modelState?.cuda_available ? '可用' : '不可用' }}</el-tag></div>
          <div class="health-status-line"><span>GPU</span><strong>{{ modelState?.cuda_name || '未检测到' }}</strong></div>
          <div class="health-status-line"><span>模型路径</span><strong style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:240px;">{{ modelState?.model_path || '未加载' }}</strong></div>
        </div>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionModeCard from '@/components/detection/DetectionModeCard.vue'
import ModelStatusBar from '@/components/shared/ModelStatusBar.vue'
import { activeModel } from '@/api/model'
import type { ModelEngineState } from '@/api/types'

const modelBarRef = ref<InstanceType<typeof ModelStatusBar> | null>(null)
const modelState = ref<ModelEngineState | null>(null)

const modes = [
  { path: '/detect/image', icon: '🖼', title: '单图检测', description: '上传单张图片，配置置信度与 IoU，查看原图/检测图对比与目标列表。适合快速验证和单张图像分析。', action: '开始单图检测' },
  { path: '/detect/batch', icon: '📦', title: '批量图片检测', description: '多张图片排队顺序推理，实时监控进度、成功率与失败样本。支持暂停、继续和终止任务。', action: '创建批量任务' },
  { path: '/detect/video', icon: '🎬', title: '视频文件检测', description: '上传视频文件创建异步任务，持续查看帧流画面、检测进度与逐帧结果。支持暂停和结束控制。', action: '上传视频检测' },
  { path: '/detect/realtime', icon: '📡', title: '实时流检测', description: '接入摄像头、RTSP 或 HTTP(S) 推流地址，实时显示 YOLO 标注画面与即时目标统计。', action: '连接实时流' },
]

const modelDisplayName = computed(() => modelState.value?.active_model?.display_name || modelState.value?.active_model?.name || '未激活')
const deviceLabel = computed(() => {
  const d = modelState.value?.device || 'auto'
  if (!d || d === 'auto') return '自动'
  if (d === 'cpu') return 'CPU'
  if (d.startsWith('cuda')) return 'GPU'
  return d
})
const warmupText = computed(() => {
  const map: Record<string, string> = { cuda_ready: 'GPU 就绪', cpu_ready: 'CPU 就绪', pending: '预热中', failed: '失败', idle: '待初始化', not_loaded: '未加载' }
  return map[modelState.value?.warmup_status || ''] || modelState.value?.warmup_status || '-'
})
const warmupTagType = computed(() => {
  const s = modelState.value?.warmup_status || ''
  if (s === 'cuda_ready' || s === 'cpu_ready') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'pending') return 'warning'
  return 'info'
})

onMounted(async () => {
  try { modelState.value = await activeModel() } catch { /* */ }
})
</script>
