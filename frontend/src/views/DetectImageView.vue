<template>
  <AppLayout>
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow dark">单图检测</span>
        <h2>图片检测与标注预览</h2>
        <p>上传一张图片，按当前参数生成检测图；AI 分析默认关闭，需要时手动开启。</p>
      </div>
      <div class="status-pills">
        <el-tag type="success">独立页面</el-tag>
        <el-tag :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '上传到历史记录' : '仅本地检测' }}</el-tag>
        <el-tag :type="params.analyze ? 'primary' : 'info'">{{ params.analyze ? 'AI 分析开启' : 'AI 分析关闭' }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench single-flow">
      <aside class="detection-control-rail panel-card">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" />
          <el-switch v-model="params.analyze" active-text="开启 AI 分析" inactive-text="关闭 AI 分析" />
        </div>
        <div class="mode-config">
          <h3>上传图片</h3>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage">
            <p>选择一张图片生成标注结果</p>
          </el-upload>
          <div class="split-actions">
            <el-button type="primary" size="large" :disabled="!imageFile || loading" :loading="loading" @click="runImage">开始检测</el-button>
            <el-button size="large" :disabled="loading || !hasResult" @click="clearResults">清除</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <main class="detection-preview-stage panel-card">
        <div class="preview-header">
          <div><span>原图 / 检测图</span><strong>{{ result ? '检测完成' : loading ? '检测中' : '等待图片' }}</strong></div>
          <el-tag :type="loading ? 'warning' : result ? 'success' : 'info'">{{ loading ? '检测中' : result ? '已完成' : '待上传' }}</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result?.original_url || result?.result_url" class="compare-grid">
            <figure><img v-if="result.original_url" :src="mediaUrl(result.original_url)" alt="原图" /><figcaption>原图</figcaption></figure>
            <figure><img v-if="result.result_url" :src="mediaUrl(result.result_url)" alt="检测图" /><figcaption>检测图</figcaption></figure>
          </div>
          <el-empty v-else :description="loading ? '正在推理，请稍候' : '上传图片后显示对比图'" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ result?.results.length ?? 0 }}</strong><span>目标数</span></div>
          <div><strong>{{ result?.duration_ms ?? 0 }}</strong><span>耗时(ms)</span></div>
          <div><strong>{{ topClass }}</strong><span>高频类别</span></div>
        </div>
      </main>
    </section>

    <section class="detection-inspector panel-card">
      <div class="inspector-header">
        <div><span class="eyebrow dark">结果详情</span><h3>单图结构化结果</h3></div>
        <el-button :disabled="loading || !hasResult" @click="clearResults">清除结果</el-button>
      </div>
      <DetectionResultTable :results="result?.results || []" />
      <AnalysisPanel v-if="result?.analysis" :analysis="result.analysis" />
      <el-empty v-else-if="result && !params.analyze" description="AI 分析未开启，本次不生成统计分析" />
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { apiMediaUrl, detectImage, type DetectParameters, type ImageDetectResult } from '@/api/detect'

const imageFile = ref<File | null>(null)
const result = ref<ImageDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive<Required<DetectParameters>>({ confidence: 0.25, iou: 0.7, save_history: true, analyze: false })
const hasResult = computed(() => Boolean(result.value))
const topClass = computed(() => {
  const rows = result.value?.results || []
  if (!rows.length) return '无'
  const counts = rows.reduce<Record<string, { count: number; label: string }>>((acc, item) => {
    acc[item.class] = acc[item.class] || { count: 0, label: item.class_zh || item.class }
    acc[item.class].count += 1
    return acc
  }, {})
  return Object.values(counts).sort((a, b) => b.count - a.count)[0].label
})

function mediaUrl(path: string) {
  return apiMediaUrl(path)
}
function selectImage(file: UploadFile) {
  imageFile.value = file.raw || null
}
function removeImage() {
  imageFile.value = null
}
async function runImage() {
  if (!imageFile.value) return
  loading.value = true
  errorText.value = ''
  try {
    result.value = await detectImage(imageFile.value, { ...params })
    ElMessage.success('单图检测已完成')
  } catch (error: any) {
    errorText.value = error?.message || '单图检测失败'
    ElMessage.error(errorText.value)
  } finally {
    loading.value = false
  }
}
async function clearResults() {
  try {
    await ElMessageBox.confirm('确认清除当前单图检测结果和预览图吗？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' })
  } catch {
    return
  }
  result.value = null
  errorText.value = ''
  ElMessage.success('检测结果已清除')
}
</script>
