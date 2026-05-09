<template>
  <AppLayout>
    <section class="detection-status-strip">
      <div>
        <span class="eyebrow dark">批量检测工作区</span>
        <h2>多图队列批处理</h2>
        <p>批量上传多张图片，逐张处理并支持暂停、继续和结束控制，预览墙实时展示检测图。</p>
      </div>
      <div class="status-pills">
        <el-tag>{{ selectedCount }} 张图片</el-tag>
        <el-tag :type="params.save_history ? 'success' : ''">{{ params.save_history ? '存入历史' : '仅本地' }}</el-tag>
      </div>
    </section>

    <section class="detection-workbench three-col">
      <!-- 左侧：文件队列 -->
      <aside class="detection-control-rail workstation-panel">
        <div class="parameter-panel">
          <h3>检测参数</h3>
          <label>置信度 {{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <label>IoU 阈值 {{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          <div style="margin-top: 14px;">
            <el-switch v-model="params.save_history" active-text="存入历史" inactive-text="仅本地" :disabled="loading" />
          </div>
        </div>
        <div style="padding: 16px; border-top: 1px solid var(--border-soft);">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: var(--color-primary-deep);">文件队列</h3>
          <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
            <p style="font-size: 13px; color: var(--color-muted);">选择多张图片批量处理</p>
          </el-upload>
          <div class="control-note">队列中：{{ selectedCount }} 张图片</div>
          <el-progress v-if="loading || result" :percentage="progress" :stroke-width="10" style="margin: 10px 0;" />
          <div class="split-actions three-actions">
            <el-button type="primary" size="small" :disabled="selectedCount === 0 || loading" @click="runBatch">开始</el-button>
            <el-button size="small" :disabled="!loading" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button size="small" type="danger" :disabled="!loading && !result" @click="endBatch">结束</el-button>
          </div>
          <p v-if="errorText" class="error-text">{{ errorText }}</p>
        </div>
      </aside>

      <!-- 中间：预览墙 -->
      <main class="detection-preview-stage workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">预览墙</span><strong style="display: block; font-size: 20px; margin-top: 2px; color: var(--color-primary-deep);">{{ previewTitle }}</strong></div>
          <el-tag :type="loading ? (paused ? 'warning' : 'success') : result ? 'success' : 'info'" size="small">{{ statusText }}</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result?.items.length" class="batch-preview-wall">
            <img v-for="item in result.items.slice(0, 9)" :key="item.file_name" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
          </div>
          <el-empty v-else :description="loading ? '批量处理中...' : '批量检测完成后显示预览墙'" />
        </div>
        <div class="preview-metrics">
          <div><strong>{{ result?.items.length ?? selectedCount }}</strong><span>图片数量</span></div>
          <div><strong>{{ targetCount }}</strong><span>总目标数</span></div>
          <div><strong>{{ progress }}%</strong><span>处理进度</span></div>
        </div>
      </main>

      <!-- 右侧：批处理状态和结果摘要 -->
      <aside class="detection-inspector workstation-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div><span style="color: var(--color-muted); font-size: 12px;">批处理摘要</span><h3 style="margin: 4px 0 0; font-size: 20px;">结果列表</h3></div>
          <el-button size="small" :disabled="loading || !result" @click="clearResults">清除</el-button>
        </div>
        <div v-if="result" style="display: grid; gap: 10px;">
          <div v-for="item in result.items" :key="item.file_name" style="padding: 10px 12px; border: 1px solid var(--border-soft); border-radius: 8px; background: var(--color-surface-alt);">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
              <strong style="font-size: 13px; color: var(--color-primary-deep); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ item.file_name }}</strong>
              <el-tag :type="item.status === 'done' ? 'success' : 'danger'" size="small">{{ item.status === 'done' ? item.results.length + '个目标' : item.status }}</el-tag>
            </div>
          </div>
        </div>
        <el-empty v-else description="等待批处理任务" />
      </aside>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
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
const statusText = computed(() => (loading.value ? (paused.value ? '已暂停' : '处理中') : result.value ? '已完成' : '待上传'))
const previewTitle = computed(() => (result.value ? `${result.value.items.length} 张图片` : loading.value ? '批量处理中' : '等待任务'))

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
function togglePause() { paused.value = !paused.value; ElMessage.info(paused.value ? '已暂停' : '已继续') }
async function endBatch() {
  try { await ElMessageBox.confirm('确认结束当前批量任务？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  ended.value = true; paused.value = false; loading.value = false
  ElMessage.warning('批量检测已结束')
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除批量检测结果？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  result.value = null; progress.value = 0; ended.value = true; errorText.value = ''
  ElMessage.success('已清除')
}
function wait(ms: number) { return new Promise((resolve) => window.setTimeout(resolve, ms)) }
</script>

<style scoped>
.detection-workbench.three-col {
  grid-template-columns: minmax(260px, 300px) minmax(0, 1.5fr) minmax(240px, 320px);
}

@media (max-width: 1200px) {
  .detection-workbench.three-col { grid-template-columns: minmax(260px, 300px) minmax(0, 1fr); }
  .detection-inspector { grid-column: 1 / -1; }
}

@media (max-width: 768px) {
  .detection-workbench.three-col { grid-template-columns: 1fr; }
}
</style>
