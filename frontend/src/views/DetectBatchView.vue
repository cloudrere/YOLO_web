<template>
  <AppLayout>
    <!-- ═══ Hero 横幅 ═══ -->
    <section class="workstation-hero flex-between">
      <div>
        <span class="eyebrow dark">视觉检测</span>
        <h2>批量检测流水线</h2>
        <p>多图队列逐张提交检测，支持暂停、继续与结束，页面状态独立保存。</p>
      </div>
      <div class="status-pills">
        <span class="pulse-dot" :class="loading ? (paused ? 'warning' : 'running') : result ? 'success' : 'idle'" />
        <el-tag :type="loading ? (paused ? 'warning' : '') : result ? 'success' : 'info'" size="large">
          {{ statusText }}
        </el-tag>
        <el-tag size="large">{{ selectedCount }} 张图片</el-tag>
        <el-tag :type="params.save_history ? 'success' : ''" size="large">
          {{ params.save_history ? '同步历史' : '本地检测' }}
        </el-tag>
      </div>
    </section>

    <!-- ═══ 双栏工作台 ═══ -->
    <section class="detection-workbench two-col">
      <!-- ── 左栏：参数面板 ── -->
      <aside class="panel-card">
        <div class="panel-section">
          <h3 class="panel-title">检测参数</h3>
          <div class="param-row">
            <label>置信度阈值 <span class="param-value">{{ params.confidence.toFixed(2) }}</span></label>
            <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          </div>
          <div class="param-row">
            <label>IoU 阈值 <span class="param-value">{{ params.iou.toFixed(2) }}</span></label>
            <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" :disabled="loading" />
          </div>
          <div class="param-row switch-row">
            <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" :disabled="loading" />
          </div>
        </div>

        <div class="panel-section">
          <h3 class="panel-title">上传批量图片</h3>
          <el-upload class="upload-area" drag multiple :auto-upload="false" :on-change="collectBatch" :on-remove="collectBatchRemove" :disabled="loading">
            <div class="upload-placeholder">
              <span class="upload-icon">＋</span>
              <p>拖拽多张图片或点击选择</p>
              <small>已选择 {{ selectedCount }} 张</small>
            </div>
          </el-upload>
        </div>

        <!-- 进度条 -->
        <div v-if="loading || result" class="panel-section">
          <div class="progress-header flex-between">
            <span class="progress-label">检测进度</span>
            <span class="progress-percent">{{ progress }}%</span>
          </div>
          <el-progress :percentage="progress" :stroke-width="10" :color="progress === 100 ? 'var(--color-success)' : 'var(--color-primary)'" />
        </div>

        <!-- 操作按钮行 -->
        <div class="split-actions three-col">
          <el-button type="primary" size="large" :disabled="selectedCount === 0 || loading" @click="runBatch">
            开始检测
          </el-button>
          <el-button size="large" :disabled="!loading" @click="togglePause">
            {{ paused ? '继续' : '暂停' }}
          </el-button>
          <el-button size="large" type="danger" :disabled="!loading && !result" @click="endBatch">
            结束
          </el-button>
        </div>

        <p v-if="errorText" class="error-text">{{ errorText }}</p>
      </aside>

      <!-- ── 右栏：队列预览 ── -->
      <main class="panel-card">
        <!-- 队列列表（模拟 BatchPipeline） -->
        <div class="panel-section">
          <h3 class="panel-title">任务队列</h3>
          <div v-if="files.length" class="queue-list">
            <TransitionGroup name="list">
              <div
                v-for="(file, i) in files"
                :key="file.name + i"
                class="queue-item"
                :class="!loading ? 'pending' : i < (result?.items?.length ?? 0) ? (result?.items[i]?.status === 'done' ? 'done' : 'failed') : i === (result?.items?.length ?? 0) ? 'running' : 'pending'"
              >
                <span class="pulse-dot sm" :class="!loading ? 'idle' : i < (result?.items?.length ?? 0) ? (result?.items[i]?.status === 'done' ? 'success' : 'danger') : i === (result?.items?.length ?? 0) ? (paused ? 'warning' : 'running') : 'idle'" />
                <span class="queue-filename">{{ file.name }}</span>
                <el-tag size="small" :type="!loading ? 'info' : i < (result?.items?.length ?? 0) ? (result?.items[i]?.status === 'done' ? 'success' : 'danger') : i === (result?.items?.length ?? 0) ? 'warning' : 'info'">
                  {{ !loading ? '等待' : i < (result?.items?.length ?? 0) ? (result?.items[i]?.status === 'done' ? '已完成' : '失败') : i === (result?.items?.length ?? 0) ? '检测中' : '等待' }}
                </el-tag>
              </div>
            </TransitionGroup>
          </div>
          <el-empty v-else description="等待添加检测文件" :image-size="64" />
        </div>

        <!-- 缩略图预览墙 -->
        <div v-if="result?.items.length" class="panel-section">
          <h3 class="panel-title">检测预览</h3>
          <div class="preview-wall">
            <img
              v-for="item in result.items.slice(0, 6)"
              :key="item.file_name"
              :src="mediaUrl(item.result_url)"
              :alt="item.file_name"
              loading="lazy"
            />
          </div>
        </div>

        <!-- 进度指标 -->
        <div class="panel-section">
          <h3 class="panel-title">进度指标</h3>
          <div class="grid three" style="margin-bottom:0;">
            <div class="metric-card compact">
              <span class="metric-label">图片数</span>
              <span class="metric-value">{{ result?.items.length ?? selectedCount }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">目标总数</span>
              <span class="metric-value">{{ targetCount }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">完成进度</span>
              <span class="metric-value">{{ progress }}%</span>
            </div>
          </div>
        </div>

        <el-empty v-if="!files.length && !result" description="批量检测完成后显示队列与预览" :image-size="80" />
      </main>
    </section>

    <!-- ═══ 底部：批量结果网格 ═══ -->
    <section v-if="result?.items.length" class="panel-card full">
      <div class="flex-between" style="margin-bottom:16px;">
        <div>
          <span class="eyebrow dark">结果详情</span>
          <h3 style="margin:4px 0 0;">批量图片检测结果</h3>
        </div>
        <el-button :disabled="loading" @click="clearResults">清除结果</el-button>
      </div>

      <div class="batch-result-grid">
        <article
          v-for="item in result.items"
          :key="item.file_name"
          class="batch-result-card"
        >
          <div class="compare-grid">
            <figure>
              <img v-if="item.original_url" :src="mediaUrl(item.original_url)" :alt="item.file_name" loading="lazy" />
              <figcaption>原图</figcaption>
            </figure>
            <figure>
              <img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" loading="lazy" />
              <figcaption>检测图</figcaption>
            </figure>
          </div>
          <div class="batch-card-body">
            <div class="flex-between" style="margin-bottom:8px;">
              <strong style="font-size:14px;color:var(--color-ink);">{{ item.file_name }}</strong>
              <el-tag :type="item.status === 'done' ? 'success' : 'danger'" size="small">
                {{ item.status === 'done' ? '已完成' : item.status }}
              </el-tag>
            </div>
            <DetectionResultTable :results="item.results" />
          </div>
        </article>
      </div>
    </section>

    <section v-else-if="!loading" class="panel-card full" style="text-align:center;">
      <el-empty description="批量检测完成后显示每张图片结果" :image-size="80" />
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

<style scoped>
/* ── Upload small override for selected count ── */
.upload-placeholder small {
  color: var(--color-primary);
  font-weight: 600;
  font-size: 12px;
}
</style>
