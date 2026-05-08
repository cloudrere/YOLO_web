<template>
  <AppLayout>
    <section class="detection-status-strip panel-card">
      <div>
        <span class="eyebrow dark">批量图片检测</span>
        <h2>多图队列检测</h2>
        <p>批量任务逐张提交，支持暂停、继续、结束，页面状态独立保存。</p>
      </div>
      <div class="status-pills">
        <el-tag>{{ selectedCount }} 张图片</el-tag>
        <el-tag :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '上传到历史记录' : '仅本地检测' }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench single-flow">
      <aside class="detection-control-rail panel-card">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="loading" />
        </div>
        <div class="mode-config">
          <h3>上传批量图片</h3>
          <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
            <p>选择多张图片批量生成标注图</p>
          </el-upload>
          <div class="control-note">已选择 {{ selectedCount }} 张图片</div>
          <el-progress v-if="loading || result" :percentage="progress" :stroke-width="12" />
          <div class="split-actions three-actions">
            <el-button type="primary" size="large" :disabled="selectedCount === 0 || loading" @click="runBatch">开始</el-button>
            <el-button size="large" :disabled="!loading" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button size="large" type="danger" :disabled="!loading && !result" @click="endBatch">结束</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <main class="detection-preview-stage panel-card">
        <div class="preview-header">
          <div><span>批量预览</span><strong>{{ previewTitle }}</strong></div>
          <el-tag :type="loading ? paused ? 'warning' : 'success' : result ? 'success' : 'info'">{{ statusText }}</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result?.items.length" class="batch-preview-wall">
            <img v-for="item in result.items.slice(0, 6)" :key="item.file_name" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
          </div>
          <el-empty v-else :description="loading ? '批量任务处理中' : '批量检测完成后显示缩略图墙'" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ result?.items.length ?? selectedCount }}</strong><span>图片数</span></div>
          <div><strong>{{ targetCount }}</strong><span>目标数</span></div>
          <div><strong>{{ progress }}%</strong><span>进度</span></div>
        </div>
      </main>
    </section>

    <section class="detection-inspector panel-card">
      <div class="inspector-header">
        <div><span class="eyebrow dark">结果详情</span><h3>批量图片结果</h3></div>
        <el-button :disabled="loading || !result" @click="clearResults">清除结果</el-button>
      </div>
      <div v-if="result" class="batch-result-grid compact-batch-grid">
        <article v-for="item in result.items" :key="item.file_name" class="batch-result-card">
          <div class="compare-grid batch-compare">
            <figure><img v-if="item.original_url" :src="mediaUrl(item.original_url)" :alt="item.file_name" /><figcaption>原图</figcaption></figure>
            <figure><img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" /><figcaption>检测图</figcaption></figure>
          </div>
          <div class="batch-card-body">
            <div class="toolbar">
              <strong>{{ item.file_name }}</strong>
              <el-tag :type="item.status === 'done' ? 'success' : 'danger'">{{ item.status === 'done' ? '已完成' : item.status }}</el-tag>
            </div>
            <DetectionResultTable :results="item.results" />
          </div>
        </article>
      </div>
      <el-empty v-else description="批量检测完成后显示每张图片结果" />
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { apiMediaUrl, detectBatch, type BatchDetectResult } from '@/api/detect'

const files = ref<File[]>([])
const result = ref<BatchDetectResult | null>(null)
const loading = ref(false)
const paused = ref(false)
const ended = ref(false)
const progress = ref(0)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
const selectedCount = computed(() => files.value.length)
const targetCount = computed(() => result.value?.items.reduce((sum, item) => sum + item.results.length, 0) ?? 0)
const statusText = computed(() => (loading.value ? (paused.value ? '已暂停' : '检测中') : result.value ? '已完成' : '待上传'))
const previewTitle = computed(() => (result.value ? `${result.value.items.length} 张图片` : loading.value ? '批量处理中' : '等待批量任务'))

function mediaUrl(path: string) {
  return apiMediaUrl(path)
}
function collectBatch(_: UploadFile, uploadFiles: UploadFile[]) {
  files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[]
}
function collectBatchRemove(_: UploadFile, uploadFiles: UploadFile[]) {
  files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[]
}
async function runBatch() {
  if (!files.value.length) return
  loading.value = true
  paused.value = false
  ended.value = false
  errorText.value = ''
  result.value = { items: [], parameters: { ...params } }
  progress.value = 0
  try {
    for (let index = 0; index < files.value.length; index += 1) {
      if (ended.value) break
      while (paused.value && !ended.value) await wait(200)
      const itemResult = await detectBatch([files.value[index]], { ...params })
      result.value.items.push(...itemResult.items)
      progress.value = Math.round(((index + 1) / files.value.length) * 100)
    }
  } catch (error: any) {
    errorText.value = error?.message || '批量检测失败'
    ElMessage.error(errorText.value)
  } finally {
    loading.value = false
    if (!ended.value && !errorText.value) ElMessage.success('批量检测已完成')
  }
}
function togglePause() {
  paused.value = !paused.value
  ElMessage.info(paused.value ? '批量检测已暂停' : '批量检测已继续')
}
async function endBatch() {
  try {
    await ElMessageBox.confirm('确认结束当前批量检测任务吗？未处理的图片将不再继续检测。', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' })
  } catch {
    return
  }
  ended.value = true
  paused.value = false
  loading.value = false
  ElMessage.warning('批量检测已结束')
}
async function clearResults() {
  try {
    await ElMessageBox.confirm('确认清除当前批量检测结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' })
  } catch {
    return
  }
  result.value = null
  progress.value = 0
  ended.value = true
  errorText.value = ''
  ElMessage.success('批量检测结果已清除')
}
function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
</script>
