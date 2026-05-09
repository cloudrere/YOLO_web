<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>批量图片检测流水线</h2>
        <p>多图队列顺序推理，实时监控进度、成功/失败统计与每张图片结果。</p>
      </div>
      <ModelStatusBar ref="modelBarRef" />
    </section>

    <!-- 三栏批量检测 -->
    <section class="detection-workbench">
      <!-- 左栏：文件队列 + 参数 -->
      <DetectionParameterPanel
        ref="paramPanelRef"
        :confidence="params.confidence" :iou="params.iou" :save-history="params.save_history"
        :running="loading" :can-run="selectedCount > 0 && !loading" run-label="开始批量检测"
        @run="runBatch"
      >
        <template #extra-params>
          <div class="param-group">
            <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">批量文件 ({{ selectedCount }})</label>
            <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
              <p style="font-size:13px;color:var(--color-muted);">选择多张图片</p>
            </el-upload>
          </div>
          <el-progress v-if="loading || result" :percentage="progress" :stroke-width="10" style="margin-top:8px;" />
        </template>
        <template #notes>
          <div style="display:flex;gap:8px;margin-top:8px;">
            <el-button size="small" :disabled="!loading" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
            <el-button size="small" type="danger" :disabled="!loading && !result" @click="endBatch">结束</el-button>
          </div>
        </template>
      </DetectionParameterPanel>

      <!-- 中栏：预览墙 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex-between">
            <span style="font-weight:700;">批量预览墙</span>
            <el-tag :type="loading ? (paused ? 'warning' : 'success') : result ? 'success' : 'info'" size="small">
              {{ statusText }}
            </el-tag>
          </div>
        </template>
        <div class="preview-wall">
          <img v-for="item in previewItems" :key="item.file_name" :src="mediaUrl(item.result_url || item.original_url)" :alt="item.file_name" />
        </div>
        <el-empty v-if="!previewItems.length" :description="loading ? '批量处理中…' : '批量检测完成后显示缩略图'" />
        <div class="result-inspector-stats" style="margin-top:12px;">
          <div class="stat-item"><span class="stat-label">图片总数</span><span class="stat-value">{{ result?.items.length || selectedCount }}</span></div>
          <div class="stat-item"><span class="stat-label">检测到目标</span><span class="stat-value">{{ targetCount }}</span></div>
          <div class="stat-item"><span class="stat-label">进度</span><span class="stat-value">{{ progress }}%</span></div>
          <div class="stat-item"><span class="stat-label">成功/失败</span><span class="stat-value" style="font-size:14px;">{{ successCount }}/{{ failCount }}</span></div>
        </div>
        <p v-if="errorText" class="error-text mt">{{ errorText }}</p>
      </el-card>

      <!-- 右栏：批量任务状态 -->
      <DetectionTaskStatus
        :status="loading ? (paused ? 'paused' : 'running') : result ? 'done' : 'idle'"
        :progress="progress"
        :error="errorText"
        :available-actions="[
          { key: 'pause', label: paused ? '继续' : '暂停', enabled: loading },
          { key: 'cancel', label: '结束任务', type: 'danger', enabled: loading || Boolean(result) },
        ]"
        @control="(key: string) => key === 'cancel' ? endBatch() : togglePause()"
      />
    </section>

    <!-- 批量结果列表 -->
    <el-card v-if="result" shadow="never" style="margin-bottom:var(--gap);">
      <template #header>
        <div class="flex-between">
          <span style="font-weight:700;">批量结果 ({{ result.items.length }})</span>
          <el-button size="small" type="danger" :disabled="loading" @click="clearResults">清除全部</el-button>
        </div>
      </template>
      <div class="grid two">
        <div v-for="item in result.items" :key="item.file_name" style="border:1px solid var(--color-border);border-radius:var(--radius-md);overflow:hidden;">
          <div class="compare-grid" style="gap:6px;">
            <figure v-if="item.original_url"><img :src="mediaUrl(item.original_url)" :alt="item.file_name" style="max-height:200px;" /><figcaption>原图</figcaption></figure>
            <figure v-if="item.result_url"><img :src="mediaUrl(item.result_url)" :alt="item.file_name" style="max-height:200px;" /><figcaption>检测图</figcaption></figure>
          </div>
          <div style="padding:10px 12px;display:flex;justify-content:space-between;align-items:center;">
            <strong style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ item.file_name }}</strong>
            <el-tag :type="item.status === 'done' ? 'success' : 'danger'" size="small">{{ item.status === 'done' ? '完成' : item.status }}</el-tag>
          </div>
          <DetectionResultTable :results="item.results" />
        </div>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionParameterPanel from '@/components/detection/DetectionParameterPanel.vue'
import DetectionTaskStatus from '@/components/detection/DetectionTaskStatus.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import ModelStatusBar from '@/components/shared/ModelStatusBar.vue'
import { apiMediaUrl, detectBatch, type BatchDetectResult } from '@/api/detect'

const modelBarRef = ref<InstanceType<typeof ModelStatusBar> | null>(null)
const paramPanelRef = ref<InstanceType<typeof DetectionParameterPanel> | null>(null)
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
const successCount = computed(() => result.value?.items.filter((i) => i.status === 'done').length ?? 0)
const failCount = computed(() => result.value?.items.filter((i) => i.status !== 'done').length ?? 0)
const previewItems = computed(() => result.value?.items.slice(0, 9) || [])

function mediaUrl(path: string) { return apiMediaUrl(path) }
function collectBatch(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
function collectBatchRemove(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
async function runBatch() {
  if (!files.value.length) return; loading.value = true; paused.value = false; ended.value = false; errorText.value = ''; result.value = { items: [], parameters: { ...params } }; progress.value = 0
  try {
    for (let index = 0; index < files.value.length; index += 1) {
      if (ended.value) break
      while (paused.value && !ended.value) await wait(200)
      const itemResult = await detectBatch([files.value[index]], { confidence: params.confidence, iou: params.iou, save_history: params.save_history })
      result.value.items.push(...itemResult.items)
      progress.value = Math.round(((index + 1) / files.value.length) * 100)
    }
  } catch (error: any) { errorText.value = error?.message || '批量检测失败'; ElMessage.error(errorText.value) } finally { loading.value = false; if (!ended.value && !errorText.value) ElMessage.success('批量检测已完成') }
}
function togglePause() { paused.value = !paused.value; ElMessage.info(paused.value ? '已暂停' : '已继续') }
async function endBatch() {
  try { await ElMessageBox.confirm('确认结束当前批量任务？', '结束确认', { type: 'warning', confirmButtonText: '确认结束', cancelButtonText: '取消' }) } catch { return }
  ended.value = true; paused.value = false; loading.value = false; ElMessage.warning('批量检测已结束')
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前批量结果？', '清除确认', { type: 'warning', confirmButtonText: '确认清除', cancelButtonText: '取消' }) } catch { return }
  result.value = null; progress.value = 0; ended.value = true; errorText.value = ''; ElMessage.success('结果已清除')
}
function wait(ms: number) { return new Promise((resolve) => window.setTimeout(resolve, ms)) }
</script>
