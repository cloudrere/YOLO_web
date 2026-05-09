<template>
  <AppLayout>
    <div class="ops-page-title">
      <h2>批量图片检测</h2>
      <div class="flex-gap">
        <el-tag size="small">{{ selectedCount }} 张图片</el-tag>
        <el-tag size="small" :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '上传到历史记录' : '仅本地检测' }}</el-tag>
      </div>
    </div>
    <p class="mb">多图队列逐张检测，支持暂停、继续、结束和进度反馈。</p>

    <div class="ops-panel cols-2-wide">
      <el-card shadow="never">
        <template #header>队列控制</template>
        <div class="ops-params">
          <label>置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <label>IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="loading" />
        </div>
        <el-divider />
        <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
          <p>选择多张图片批量生成标注图</p>
        </el-upload>
        <div class="mb" style="margin-top:8px">已选择 {{ selectedCount }} 张图片</div>
        <el-progress v-if="loading || result" :percentage="progress" :stroke-width="8" class="ops-progress" />
        <div class="flex-gap">
          <el-button type="primary" :disabled="selectedCount === 0 || loading" @click="runBatch">开始</el-button>
          <el-button :disabled="!loading" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button type="danger" :disabled="!loading && !result" @click="endBatch">结束</el-button>
        </div>
        <p v-if="errorText" class="text-danger">{{ errorText }}</p>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex-between">
            <span>{{ previewTitle }}</span>
            <el-tag size="small" :type="loading ? (paused ? 'warning' : 'success') : result ? 'success' : 'info'">{{ statusText }}</el-tag>
          </div>
        </template>
        <div class="ops-preview">
          <div v-if="result?.items.length" class="ops-thumbs">
            <img v-for="item in result.items.slice(0, 12)" :key="item.file_name" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
          </div>
          <el-empty v-else :description="loading ? '批量任务处理中' : '批量检测完成后显示缩略图'" />
        </div>
        <div class="ops-metrics cols-3" style="margin-top:12px">
          <div class="ops-metric"><span class="metric-label">图片数</span><span class="metric-value text-mono" style="font-size:18px">{{ result?.items.length ?? selectedCount }}</span></div>
          <div class="ops-metric"><span class="metric-label">目标数</span><span class="metric-value text-mono" style="font-size:18px">{{ targetCount }}</span></div>
          <div class="ops-metric"><span class="metric-label">进度</span><span class="metric-value text-mono" style="font-size:18px">{{ progress }}%</span></div>
        </div>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="flex-between">
          <span>批量图片结果</span>
          <el-button size="small" :disabled="loading || !result" @click="clearResults">清除结果</el-button>
        </div>
      </template>
      <div v-if="result" class="ops-result-grid">
        <article v-for="item in result.items" :key="item.file_name">
          <el-card shadow="never">
            <div class="ops-compare">
              <figure><img v-if="item.original_url" :src="mediaUrl(item.original_url)" :alt="item.file_name" /><figcaption>原图</figcaption></figure>
              <figure><img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" /><figcaption>检测图</figcaption></figure>
            </div>
            <div class="flex-between" style="margin-top:6px">
              <strong style="font-size:12px">{{ item.file_name }}</strong>
              <el-tag size="small" :type="item.status === 'done' ? 'success' : 'danger'">{{ item.status === 'done' ? '已完成' : item.status }}</el-tag>
            </div>
            <DetectionResultTable :results="item.results" />
          </el-card>
        </article>
      </div>
      <el-empty v-else description="批量检测完成后显示每张图片结果" />
    </el-card>
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

function mediaUrl(path: string) { return apiMediaUrl(path) }
function collectBatch(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
function collectBatchRemove(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
async function runBatch() {
  if (!files.value.length) return
  loading.value = true; paused.value = false; ended.value = false; errorText.value = ''
  result.value = { items: [], parameters: { ...params } }; progress.value = 0
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
function togglePause() { paused.value = !paused.value; ElMessage.info(paused.value ? '批量检测已暂停' : '批量检测已继续') }
async function endBatch() {
  try { await ElMessageBox.confirm('确认结束当前批量检测任务吗？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  ended.value = true; paused.value = false; loading.value = false; ElMessage.warning('批量检测已结束')
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前批量检测结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  result.value = null; progress.value = 0; ended.value = true; errorText.value = ''; ElMessage.success('批量检测结果已清除')
}
function wait(ms: number) { return new Promise((resolve) => window.setTimeout(resolve, ms)) }
</script>
