<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>批量样本处理台</h1>
        <p>多图队列逐张检测，支持暂停/继续/结束，实时进度反馈。</p>
      </div>
      <div class="ws-tags">
        <el-tag size="small">{{ selectedCount }} 张图片</el-tag>
        <el-tag size="small" :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '保存历史' : '仅本地' }}</el-tag>
      </div>
    </div>

    <div class="ws-panel-2">
      <!-- 队列控制面板 -->
      <div class="ws-tool-panel">
        <div class="panel-label">检测参数</div>
        <div class="ws-param-group">
          <label>置信度 <span>{{ params.confidence.toFixed(2) }}</span></label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
        </div>
        <div class="ws-param-group">
          <label>IoU 阈值 <span>{{ params.iou.toFixed(2) }}</span></label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
        </div>
        <div class="ws-param-group">
          <el-switch v-model="params.save_history" active-text="保存历史" inactive-text="仅本地" :disabled="loading" />
        </div>
        <div class="ws-tool-divider"></div>
        <div class="panel-label">样本队列</div>
        <el-upload drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
          <p>选择多张图片</p>
        </el-upload>
        <div style="margin-top:6px;font-size:11px;color:var(--text-muted)">已选择 {{ selectedCount }} 张</div>
        <el-progress v-if="loading || result" :percentage="progress" :stroke-width="6" class="ws-progress" />
        <div class="flex-gap" style="margin-top:8px">
          <el-button type="primary" :disabled="selectedCount === 0 || loading" @click="runBatch">开始</el-button>
          <el-button :disabled="!loading" @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button type="danger" :disabled="!loading && !result" @click="endBatch">结束</el-button>
        </div>
        <p v-if="errorText" class="text-danger" style="margin-top:8px">{{ errorText }}</p>
      </div>

      <!-- 预览与结果 -->
      <div>
        <div class="ws-preview-stage" style="margin-bottom:10px">
          <div class="ws-preview-header">
            <span>{{ previewTitle }}</span>
            <el-tag size="small" :type="loading ? (paused ? 'warning' : 'success') : result ? 'success' : 'info'">{{ statusText }}</el-tag>
          </div>
          <div class="ws-preview-canvas" style="aspect-ratio:auto;min-height:180px">
            <div v-if="result?.items.length" class="ws-thumb-grid" style="padding:10px">
              <img v-for="item in result.items.slice(0, 12)" :key="item.file_name" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
            </div>
            <span v-else style="color:var(--text-muted);font-size:13px">{{ loading ? '处理中…' : '完成后显示缩略图' }}</span>
          </div>
          <div class="ws-preview-footer">
            <div class="foot-stat"><span class="stat-num">{{ result?.items.length ?? selectedCount }}</span><span class="stat-label">图片数</span></div>
            <div class="foot-stat"><span class="stat-num">{{ targetCount }}</span><span class="stat-label">目标数</span></div>
            <div class="foot-stat"><span class="stat-num">{{ progress }}%</span><span class="stat-label">进度</span></div>
          </div>
        </div>

        <div class="ws-card" v-if="result?.items.length">
          <div class="ws-card-header">
            <span>处理结果</span>
            <el-button size="small" :disabled="loading" @click="clearResults">清除</el-button>
          </div>
          <div class="ws-card-body">
            <div class="ws-result-grid">
              <div v-for="item in result.items" :key="item.file_name" class="ws-batch-card">
                <div class="batch-header">
                  <strong style="font-size:11px">{{ item.file_name }}</strong>
                  <el-tag size="small" :type="item.status === 'done' ? 'success' : 'danger'">{{ item.status === 'done' ? 'OK' : item.status }}</el-tag>
                </div>
                <div class="compare-split" style="aspect-ratio:2/1;background:#000;display:grid;grid-template-columns:1fr 1fr">
                  <img v-if="item.original_url" :src="mediaUrl(item.original_url)" :alt="item.file_name" style="width:100%;height:100%;object-fit:contain" />
                  <img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" style="width:100%;height:100%;object-fit:contain;border-left:1px solid rgba(255,255,255,0.1)" />
                </div>
                <div style="padding:6px 8px;font-size:11px">
                  <div v-for="(r, i) in item.results" :key="i" class="ws-detection-row">
                    <span class="det-class">{{ r.class_zh || r.class }}</span>
                    <span class="det-conf">{{ (r.confidence * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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
const previewTitle = computed(() => (result.value ? `${result.value.items.length} 张` : loading.value ? '处理中' : '等待任务'))

function mediaUrl(path: string) { return apiMediaUrl(path) }
function collectBatch(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
function collectBatchRemove(_: UploadFile, uploadFiles: UploadFile[]) { files.value = uploadFiles.map((item) => item.raw).filter(Boolean) as File[] }
async function runBatch() {
  if (!files.value.length) return
  loading.value = true; paused.value = false; ended.value = false; errorText.value = ''; result.value = { items: [], parameters: { ...params } }; progress.value = 0
  try {
    for (let index = 0; index < files.value.length; index += 1) {
      if (ended.value) break
      while (paused.value && !ended.value) await wait(200)
      const itemResult = await detectBatch([files.value[index]], { ...params })
      result.value.items.push(...itemResult.items); progress.value = Math.round(((index + 1) / files.value.length) * 100)
    }
  } catch (error: any) { errorText.value = error?.message || '批量检测失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false; if (!ended.value && !errorText.value) ElMessage.success('批量检测已完成') }
}
function togglePause() { paused.value = !paused.value; ElMessage.info(paused.value ? '已暂停' : '已继续') }
async function endBatch() { try { await ElMessageBox.confirm('确认结束当前批量任务？未处理的图片不再检测。', '结束确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; ended.value = true; paused.value = false; loading.value = false; ElMessage.warning('批量检测已结束') }
async function clearResults() { try { await ElMessageBox.confirm('确认清除当前批量检测结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; result.value = null; progress.value = 0; ended.value = true; errorText.value = ''; ElMessage.success('结果已清除') }
function wait(ms: number) { return new Promise((resolve) => window.setTimeout(resolve, ms)) }
</script>
