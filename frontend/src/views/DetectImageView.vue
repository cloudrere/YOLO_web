<template>
  <AppLayout>
    <section class="detection-status-strip">
      <div>
        <span class="eyebrow dark">单图检测工作区</span>
        <h2>图片检测与标注预览</h2>
        <p>上传单张图片，设置检测参数，对比原图与检测结果，查看结构化目标列表。</p>
      </div>
      <div class="status-pills">
        <el-tag>{{ params.save_history ? '存入历史' : '仅本地' }}</el-tag>
        <el-tag :type="result ? 'success' : 'info'">{{ result ? '已完成' : '就绪' }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench three-col">
      <!-- 左侧：参数 & 上传面板 -->
      <aside class="detection-control-rail workstation-panel">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度 {{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" />
          <label>IoU 阈值 {{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" />
          <div style="margin-top: 14px;">
            <el-switch v-model="params.save_history" active-text="存入历史" inactive-text="仅本地" />
          </div>
        </div>
        <div style="padding: 16px; border-top: 1px solid var(--border-soft);">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: var(--color-primary-deep);">上传图片</h3>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage">
            <p style="font-size: 13px; color: var(--color-muted);">选择一张图片生成标注结果</p>
          </el-upload>
          <div class="split-actions" style="margin-top: 14px;">
            <el-button type="primary" :disabled="!imageFile || loading" :loading="loading" @click="runImage">开始检测</el-button>
            <el-button :disabled="loading || !hasResult" @click="clearResults">清除</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <!-- 中间：图像对比主画布 -->
      <main class="detection-preview-stage workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">预览画布</span><strong style="display: block; font-size: 20px; margin-top: 2px; color: var(--color-primary-deep);">{{ result ? '检测完成' : loading ? '推理中...' : '等待图片' }}</strong></div>
          <el-tag :type="loading ? 'warning' : result ? 'success' : 'info'" size="small">{{ loading ? '推理中' : result ? '已完成' : '待上传' }}</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result?.original_url || result?.result_url" class="compare-grid">
            <figure>
              <img v-if="result.original_url" :src="mediaUrl(result.original_url)" alt="原图" />
              <figcaption>原始图片</figcaption>
            </figure>
            <figure>
              <img v-if="result.result_url" :src="mediaUrl(result.result_url)" alt="检测图" />
              <figcaption>检测标注</figcaption>
            </figure>
          </div>
          <el-empty v-else :description="loading ? '正在推理，请稍候...' : '上传图片后开始检测'" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ result?.results.length ?? 0 }}</strong><span>检测目标数</span></div>
          <div><strong>{{ result?.duration_ms ?? 0 }} ms</strong><span>推理耗时</span></div>
          <div><strong>{{ topClass }}</strong><span>高频类别</span></div>
        </div>
      </main>

      <!-- 右侧：结果检查器 -->
      <aside class="detection-inspector workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">结果检查器</span><h3 style="margin: 4px 0 0; font-size: 20px;">结构化结果</h3></div>
          <el-button size="small" :disabled="loading || !hasResult" @click="clearResults">清除</el-button>
        </div>
        <DetectionResultTable :results="result?.results || []" />
      </aside>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { apiMediaUrl, detectImage, type ImageDetectResult } from '@/api/detect'

const imageFile = ref<File | null>(null)
const result = ref<ImageDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
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

function mediaUrl(path: string) { return apiMediaUrl(path) }
function selectImage(file: UploadFile) { imageFile.value = file.raw || null }
function removeImage() { imageFile.value = null }
async function runImage() {
  if (!imageFile.value) return
  loading.value = true; errorText.value = ''
  try {
    result.value = await detectImage(imageFile.value, { ...params })
    ElMessage.success('单图检测已完成')
  } catch (error: any) {
    errorText.value = error?.message || '单图检测失败'
    ElMessage.error(errorText.value)
  } finally { loading.value = false }
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前检测结果？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  result.value = null; errorText.value = ''
  ElMessage.success('检测结果已清除')
}
</script>

<style scoped>
.detection-workbench.three-col {
  grid-template-columns: minmax(260px, 300px) minmax(0, 1.5fr) minmax(240px, 320px);
}

@media (max-width: 1200px) {
  .detection-workbench.three-col {
    grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  }
  .detection-inspector { grid-column: 1 / -1; }
}

@media (max-width: 768px) {
  .detection-workbench.three-col { grid-template-columns: 1fr; }
}
</style>
