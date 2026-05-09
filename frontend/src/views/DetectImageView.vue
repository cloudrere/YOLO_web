<template>
  <AppLayout>
    <!-- ═══ Hero 横幅 ═══ -->
    <section class="workstation-hero flex-between">
      <div>
        <span class="eyebrow dark">视觉检测</span>
        <h2>单图动态检测工作台</h2>
        <p>上传一张图片，实时推理生成标注图与结构化检测结果，支持保存到检测历史。</p>
      </div>
      <div class="status-pills">
        <span class="pulse-dot" :class="loading ? 'running' : result ? 'success' : 'idle'" />
        <el-tag :type="loading ? 'warning' : result ? 'success' : 'info'" size="large">
          {{ loading ? '推理中' : result ? '已完成' : '待上传' }}
        </el-tag>
        <el-tag :type="params.save_history ? 'success' : ''" size="large">
          {{ params.save_history ? '同步历史' : '本地检测' }}
        </el-tag>
      </div>
    </section>

    <!-- ═══ 三栏检测工作台 ═══ -->
    <section class="detection-workbench">
      <!-- ── 左栏：参数面板 ── -->
      <aside class="panel-card stagger-container">
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
          <h3 class="panel-title">上传图片</h3>
          <el-upload class="upload-area" drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage" :disabled="loading">
            <div class="upload-placeholder">
              <span class="upload-icon">＋</span>
              <p>拖拽图片到此处或点击选择</p>
              <small>支持 JPG / PNG / WebP</small>
            </div>
          </el-upload>
        </div>

        <div class="split-actions">
          <el-button type="primary" size="large" :disabled="!imageFile || loading" :loading="loading" @click="runImage">
            {{ loading ? '检测中…' : '开始检测' }}
          </el-button>
          <el-button size="large" :disabled="loading || !hasResult" @click="clearResults">清除结果</el-button>
        </div>

        <p v-if="errorText" class="error-text">{{ errorText }}</p>
      </aside>

      <!-- ── 中栏：检测画布 ── -->
      <main class="detect-canvas panel-card" :class="{ 'has-image': result?.original_url || result?.result_url }">
        <!-- 加载态：扫描动画 -->
        <div v-if="loading" class="scan-overlay">
          <div class="scan-line" />
        </div>
        <div v-if="loading" class="canvas-state scanning">
          <div class="scan-label pulse-glow">正在推理检测中…</div>
        </div>

        <!-- 结果态：原图 / 检测图对比 -->
        <div v-else-if="result && (result.original_url || result.result_url)" class="compare-grid">
          <figure>
            <img v-if="result.original_url" :src="mediaUrl(result.original_url)" alt="原图" />
            <figcaption>原图</figcaption>
          </figure>
          <figure>
            <img v-if="result.result_url" :src="mediaUrl(result.result_url)" alt="检测图" />
            <figcaption>检测图</figcaption>
          </figure>
        </div>

        <!-- 空态 -->
        <div v-else class="canvas-state empty">
          <div class="empty-icon-box">
            <svg width="56" height="56" viewBox="0 0 56 56" fill="none" style="opacity:0.25;">
              <rect x="6" y="6" width="44" height="44" rx="6" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4" />
              <rect x="16" y="16" width="24" height="16" rx="3" stroke="currentColor" stroke-width="1.5" />
              <circle cx="28" cy="24" r="5" stroke="currentColor" stroke-width="1.5" />
              <path d="M16 40l8-8 4 4 8-8 4 4v8H16z" stroke="currentColor" stroke-width="1.5" fill="none" />
            </svg>
          </div>
          <h3>等待图片上传</h3>
          <p>选择图片后点击开始检测，标注结果将展示在此区域</p>
        </div>
      </main>

      <!-- ── 右栏：检测结果检视器 ── -->
      <aside class="panel-card">
        <div class="panel-section">
          <h3 class="panel-title">检测概要</h3>
          <div class="grid three" style="margin-bottom:0;">
            <div class="metric-card compact">
              <span class="metric-label">目标总数</span>
              <span class="metric-value">{{ result?.results.length ?? 0 }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">耗时(ms)</span>
              <span class="metric-value">{{ result?.duration_ms ?? 0 }}</span>
            </div>
            <div class="metric-card compact">
              <span class="metric-label">高频类别</span>
              <span class="metric-value" style="font-size:18px;">{{ topClass }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section" v-if="result?.results.length">
          <h3 class="panel-title">类别标签</h3>
          <div class="flex-wrap">
            <el-tag
              v-for="(item, i) in classTags" :key="i"
              size="small" type="success"
            >{{ item.name }} {{ item.count }}</el-tag>
          </div>
        </div>

        <div class="panel-section table-scroll" v-if="result?.results.length">
          <h3 class="panel-title">结构化结果</h3>
          <DetectionResultTable :results="result.results" />
        </div>

        <div class="panel-section" v-else-if="!loading">
          <el-empty description="检测完成后显示结果概览" :image-size="80" />
        </div>
      </aside>
    </section>

    <!-- ═══ 底部：全宽结构化结果表 ═══ -->
    <section v-if="hasResult" class="panel-card full">
      <div class="flex-between" style="margin-bottom:16px;">
        <div>
          <span class="eyebrow dark">结果详情</span>
          <h3 style="margin:4px 0 0;">单图结构化检测结果</h3>
        </div>
        <el-button :disabled="loading" @click="clearResults">清除结果</el-button>
      </div>
      <DetectionResultTable :results="result?.results || []" />
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
const classTags = computed(() => {
  const rows = result.value?.results || []
  if (!rows.length) return []
  const map = new Map<string, number>()
  rows.forEach(r => { const k = r.class_zh || r.class; map.set(k, (map.get(k) || 0) + 1) })
  return Array.from(map.entries()).map(([name, count]) => ({ name, count }))
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

<style scoped>
/* ── Canvas overrides ── */
.detect-canvas {
  min-height: 420px;
}

/* ── Compare grid tweaks ── */
.compare-grid {
  padding: 0;
  width: 100%;
}
.compare-grid img {
  max-height: 380px;
}
</style>
