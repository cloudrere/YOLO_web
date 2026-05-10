<template>
  <AppLayout>
    <section class="training-hero panel-card">
      <div>
        <span class="eyebrow dark">YOLO results.csv</span>
        <h2>训练曲线与质量诊断</h2>
        <p>上传或选择 YOLO 训练生成的 results.csv，查看 Precision、Recall、mAP、Loss、学习率与 AI 训练建议。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="summary ? 'success' : 'info'">{{ summary ? '已加载摘要' : '等待 CSV' }}</el-tag>
        <el-tag :type="assistantStatus?.configured ? 'success' : 'warning'">{{ aiStatusText }}</el-tag>
      </div>
    </section>

    <section class="training-upload-row">
      <el-card shadow="never" class="upload-card training-control-panel">
        <template #header>训练数据</template>
        <div class="training-upload-inline">
          <el-upload drag accept=".csv" :auto-upload="false" :limit="1" :on-change="selectCsv" :on-remove="removeCsv">
            <p>拖拽或选择 YOLO results.csv 文件</p>
          </el-upload>
          <div class="training-upload-actions">
            <el-button type="primary" :loading="uploading" :disabled="!csvFile || uploading" @click="uploadCsv">上传并分析</el-button>
            <el-button :loading="loadingFiles" @click="loadFiles">刷新列表</el-button>
            <el-button :disabled="!summary" @click="exportReport">导出报告</el-button>
            <el-button type="danger" plain :disabled="!canManageTraining || !selectedName" @click="removeCurrentAnalysis">删除当前分析</el-button>
            <el-button type="danger" :disabled="!canManageTraining || !files.length" @click="clearAllAnalyses">清空全部</el-button>
          </div>
          <div class="training-upload-select">
            <el-select v-model="selectedName" filterable placeholder="选择已上传 CSV" class="full" :loading="loadingFiles" @change="loadSummary">
              <el-option v-for="item in files" :key="item.name" :label="item.name" :value="item.name" />
            </el-select>
          </div>
        </div>
        <div class="table-scroll training-file-table">
          <el-table v-loading="loadingFiles" :data="files" empty-text="暂无训练 CSV" size="small" @row-click="selectFileRow">
            <el-table-column prop="name" label="文件名" min-width="170" />
            <el-table-column prop="rows" label="Epoch" width="90" />
            <el-table-column prop="best_epoch" label="最佳" width="90" />
          </el-table>
        </div>
      </el-card>
    </section>

    <section class="training-summary-row">
      <Transition name="list">
        <div v-if="summary" key="summary" class="training-kpi-strip">
          <div v-for="(card, i) in summaryCards" :key="card.label" class="kpi-item" :style="{ animationDelay: i * 80 + 'ms' }">
            <span class="kpi-label">{{ card.label }}</span>
            <strong class="kpi-value"><AnimatedNumber :value="typeof card.value === 'number' ? card.value : 0" /></strong>
            <small class="kpi-desc">{{ card.desc }}</small>
          </div>
        </div>
      </Transition>
      <div class="training-warning-inline">
        <div v-if="summary?.warnings.length" class="training-warning-list">
          <div v-for="(item, i) in summary.warnings" :key="i" :style="{ animationDelay: i * 80 + 'ms' }">{{ item }}</div>
        </div>
        <el-empty v-else :description="summary ? '无明显风险' : '加载 CSV 后显示'" :image-size="32" />
      </div>
    </section>

    <section class="grid two training-chart-grid stagger-container">
      <MotionPanel v-for="(panel, i) in chartPanels" :key="panel.title" effect="glow" :style="{ animationDelay: i * 60 + 'ms' }">
        <el-card shadow="never" class="panel-card chart-panel">
          <template #header>{{ panel.title }}</template>
          <div :ref="(el) => { if (el && panel.setRef) panel.setRef(el as HTMLElement) }" v-loading="summaryLoading" class="chart"></div>
        </el-card>
      </MotionPanel>
    </section>

    <el-card shadow="never" class="panel-card training-ai-panel">
      <template #header>
        <div class="toolbar">
          <span>AI 训练分析</span>
          <el-button type="primary" :loading="aiLoading" :disabled="!canUseAi" @click="generateAiReport">生成 AI 报告</el-button>
        </div>
      </template>
      <div class="training-ai-state">
        <el-tag :type="canUseAi ? 'success' : 'warning'">{{ aiActionText }}</el-tag>
        <span>AI 会基于当前 summary 生成训练质量分析、风险判断和下一步优化建议。</span>
      </div>
      <Transition name="list">
        <div v-if="aiReport" key="report" class="assistant-answer training-ai-answer">{{ aiReport }}</div>
      </Transition>
      <el-empty v-if="!aiReport" description="点击生成后显示 AI 训练报告" />
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnimatedNumber from '@/components/common/AnimatedNumber.vue'
import MotionPanel from '@/components/common/MotionPanel.vue'
import { getAssistantStatus, type AssistantStatus } from '@/api/assistant'
import {
  clearTrainingAnalyses,
  deleteTrainingAnalysis,
  exportTrainingReport,
  getTrainingAiReport,
  getTrainingSummary,
  listTrainingFiles,
  uploadTrainingResults,
  type TrainingAnalysisFile,
  type TrainingAnalysisSummary,
} from '@/api/trainingAnalysis'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const files = ref<TrainingAnalysisFile[]>([])
const csvFile = ref<File | null>(null)
const selectedName = ref('')
const summary = ref<TrainingAnalysisSummary | null>(null)
const assistantStatus = ref<AssistantStatus | null>(null)
const aiReport = ref('')
const loadingFiles = ref(false)
const uploading = ref(false)
const summaryLoading = ref(false)
const aiLoading = ref(false)
const precisionRecallEl = ref<HTMLElement | null>(null)
const mapEl = ref<HTMLElement | null>(null)
const lossEl = ref<HTMLElement | null>(null)
const radarEl = ref<HTMLElement | null>(null)
const barEl = ref<HTMLElement | null>(null)
const lrEl = ref<HTMLElement | null>(null)
let charts: echarts.ECharts[] = []

const summaryCards = computed(() => [
  { label: '总 Epoch', value: summary.value?.epochs.length ?? 0, desc: summary.value?.name || '上传 results.csv 后解析' },
  { label: '最佳 Epoch', value: summary.value?.best_epoch ?? 0, desc: '按 mAP50 峰值定位' },
  { label: '最佳 mAP50', value: formatRatioNumber(summary.value?.best_map50), desc: '训练过程最高 mAP50' },
  { label: '最终 Recall', value: formatRatioNumber(summary.value?.final_metrics.recall), desc: '最后一轮召回率' },
])
const canUseAi = computed(() => Boolean(summary.value && auth.hasPermission('assistant:use') && assistantStatus.value?.configured))
const canManageTraining = computed(() => auth.hasPermission('history:manage'))
const aiStatusText = computed(() => {
  if (!auth.hasPermission('assistant:use')) return '无 AI 权限'
  return assistantStatus.value?.configured ? `AI 已配置：${assistantStatus.value.model}` : 'AI 未配置'
})
const aiActionText = computed(() => {
  if (!summary.value) return '请先加载训练摘要'
  if (!auth.hasPermission('assistant:use')) return '当前账号无 AI 助手权限'
  if (!assistantStatus.value?.configured) return '后端未配置 AI_ASSISTANT_API_KEY'
  return '可生成训练分析报告'
})
const chartPanels = computed(() => [
  { title: 'Precision / Recall 曲线', setRef: (el: HTMLElement) => { precisionRecallEl.value = el } },
  { title: 'mAP 曲线', setRef: (el: HTMLElement) => { mapEl.value = el } },
  { title: '训练 / 验证 Loss 曲线', setRef: (el: HTMLElement) => { lossEl.value = el } },
  { title: '最终指标雷达图', setRef: (el: HTMLElement) => { radarEl.value = el } },
  { title: '最终 Loss 柱状对比', setRef: (el: HTMLElement) => { barEl.value = el } },
  { title: '学习率曲线', setRef: (el: HTMLElement) => { lrEl.value = el } },
])

onMounted(async () => {
  window.addEventListener('resize', resizeCharts)
  await Promise.all([loadFiles(), loadAssistantStatus()])
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})

function selectCsv(file: UploadFile) {
  const raw = file.raw || null
  if (raw && !raw.name.toLowerCase().endsWith('.csv')) {
    ElMessage.warning('仅支持 CSV 文件')
    csvFile.value = null
    return
  }
  csvFile.value = raw
}
function removeCsv() {
  csvFile.value = null
}
async function uploadCsv() {
  if (!csvFile.value) return
  uploading.value = true
  try {
    const data = await uploadTrainingResults(csvFile.value)
    selectedName.value = data.file.name
    summary.value = data.summary
    aiReport.value = ''
    await loadFiles(false)
    await nextTick()
    renderCharts()
    ElMessage.success('训练 CSV 已上传并解析')
  } finally {
    uploading.value = false
  }
}
async function loadFiles(autoLoad = true) {
  loadingFiles.value = true
  try {
    const data = await listTrainingFiles()
    files.value = data.items
    if (autoLoad && !summary.value && data.items.length) {
      selectedName.value = data.items[0].name
      await loadSummary(selectedName.value)
    }
  } finally {
    loadingFiles.value = false
  }
}
async function loadAssistantStatus() {
  if (!auth.hasPermission('assistant:use')) return
  assistantStatus.value = await getAssistantStatus()
}
async function loadSummary(name: string) {
  if (!name) return
  summaryLoading.value = true
  try {
    summary.value = await getTrainingSummary(name)
    selectedName.value = name
    aiReport.value = ''
    await nextTick()
    renderCharts()
  } finally {
    summaryLoading.value = false
  }
}
function selectFileRow(row: TrainingAnalysisFile) {
  loadSummary(row.name)
}
async function generateAiReport() {
  if (!summary.value) return
  aiLoading.value = true
  try {
    const data = await getTrainingAiReport(summary.value.name, summary.value)
    aiReport.value = data.answer
    ElMessage.success('AI 训练分析已生成')
  } finally {
    aiLoading.value = false
  }
}
async function exportReport() {
  if (!summary.value) return
  const response = await exportTrainingReport(summary.value.name)
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `${summary.value.name.replace(/\.csv$/i, '')}_training_report.txt`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('训练分析报告已导出')
}
async function removeCurrentAnalysis() {
  if (!selectedName.value) return
  try {
    await ElMessageBox.confirm(`确认删除当前训练分析 ${selectedName.value} 吗？文件与数据库记录都会被移除。`, '删除当前分析', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteTrainingAnalysis(selectedName.value)
  ElMessage.success('当前训练分析已删除')
  summary.value = null
  aiReport.value = ''
  selectedName.value = ''
  disposeCharts()
  await loadFiles()
}
async function clearAllAnalyses() {
  if (!files.value.length) return
  try {
    await ElMessageBox.confirm(`确认清空全部 ${files.value.length} 条训练分析吗？所有 CSV 文件和数据库记录都会被移除。`, '清空全部分析', { type: 'warning', confirmButtonText: '确认清空', cancelButtonText: '取消' })
  } catch {
    return
  }
  await clearTrainingAnalyses()
  ElMessage.success('全部训练分析已清空')
  summary.value = null
  aiReport.value = ''
  selectedName.value = ''
  files.value = []
  disposeCharts()
}
function renderCharts() {
  disposeCharts()
  if (!summary.value) return
  renderPrecisionRecallChart()
  renderMapChart()
  renderLossChart()
  renderRadarChart()
  renderBarChart()
  renderLearningRateChart()
}
function makeChart(el: HTMLElement | null) {
  if (!el) return null
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}
function disposeCharts() {
  charts.forEach((chart) => chart.dispose())
  charts = []
}
function resizeCharts() {
  charts.forEach((chart) => chart.resize())
}
function chartBaseGrid(top = 34) {
  return { left: 48, right: 24, top, bottom: 38 }
}
function toEpochSeries(values: number[]) {
  const epochs = summary.value?.epochs || []
  return epochs.map((epoch, index) => [epoch, values[index]])
}
function lineSeries(name: string, values: number[], extra: Record<string, unknown> = {}) {
  return {
    name,
    type: 'line',
    smooth: true,
    showSymbol: false,
    symbol: 'circle',
    symbolSize: 5,
    connectNulls: true,
    lineStyle: { width: 3 },
    emphasis: { focus: 'series' },
    data: toEpochSeries(values),
    ...extra,
  }
}
function renderPrecisionRecallChart() {
  const chart = makeChart(precisionRecallEl.value)
  const data = summary.value
  if (!chart || !data) return
  chart.setOption({
    color: ['#2563eb', '#ea580c'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: chartBaseGrid(46),
    xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' },
    yAxis: { type: 'value', max: 1 },
    series: [
      lineSeries('Precision', data.precision),
      lineSeries('Recall', data.recall),
    ],
  })
}
function renderMapChart() {
  const chart = makeChart(mapEl.value)
  const data = summary.value
  if (!chart || !data) return
  chart.setOption({
    color: ['#2563eb', '#0891b2'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: chartBaseGrid(46),
    xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' },
    yAxis: { type: 'value', max: 1 },
    series: [
      lineSeries('mAP50', data.map50, { areaStyle: { opacity: 0.12 } }),
      lineSeries('mAP50-95', data.map5095, { areaStyle: { opacity: 0.08 } }),
    ],
  })
}
function renderLossChart() {
  const chart = makeChart(lossEl.value)
  const data = summary.value
  if (!chart || !data) return
  chart.setOption({
    color: ['#2563eb', '#7c3aed', '#0891b2', '#ea580c', '#dc2626', '#d97706'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: chartBaseGrid(54),
    xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' },
    yAxis: { type: 'value' },
    series: [
      lineSeries('Train Box', data.train_box_loss),
      lineSeries('Train Cls', data.train_cls_loss),
      lineSeries('Train DFL', data.train_dfl_loss),
      lineSeries('Val Box', data.val_box_loss),
      lineSeries('Val Cls', data.val_cls_loss),
      lineSeries('Val DFL', data.val_dfl_loss),
    ],
  })
}
function renderRadarChart() {
  const chart = makeChart(radarEl.value)
  const data = summary.value
  if (!chart || !data) return
  const values = data.radar.map((item) => Number(item.value) || 0)
  chart.setOption({
    color: ['#2563eb'],
    tooltip: {},
    radar: { indicator: data.radar.map((item) => ({ name: String(item.name), max: 1 })), radius: '66%' },
    series: [{ type: 'radar', areaStyle: { opacity: 0.18 }, data: [{ name: '最终指标', value: values }] }],
  })
}
function renderBarChart() {
  const chart = makeChart(barEl.value)
  const data = summary.value
  if (!chart || !data) return
  chart.setOption({
    color: ['#ea580c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 112, right: 18, top: 20, bottom: 28 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.bar_metrics.map((item) => item.name) },
    series: [{ type: 'bar', barWidth: 20, data: data.bar_metrics.map((item) => Number(item.value) || 0) }],
  })
}
function renderLearningRateChart() {
  const chart = makeChart(lrEl.value)
  const data = summary.value
  if (!chart || !data) return
  chart.setOption({
    color: ['#2563eb', '#ea580c', '#0891b2'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: chartBaseGrid(46),
    xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' },
    yAxis: { type: 'value' },
    series: [
      lineSeries('lr/pg0', data.lr_pg0),
      lineSeries('lr/pg1', data.lr_pg1),
      lineSeries('lr/pg2', data.lr_pg2),
    ],
  })
}
function formatRatio(value?: number | null) {
  if (value === null || value === undefined) return '-'
  return `${(Number(value) * 100).toFixed(1)}%`
}
function formatRatioNumber(value?: number | null): number {
  if (value === null || value === undefined) return 0
  return Number(value)
}
</script>

<style scoped>
/* 训练分析 Hero */
.training-hero {
  background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 50%, #fdf4ff 100%);
  border: 1px solid #c7d2fe;
}

/* 训练控制面板 — 独立一行 */
.training-upload-row {
  margin-bottom: var(--gap);
}

.training-upload-inline {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
}

.training-upload-inline :deep(.el-upload) {
  width: auto;
}

.training-upload-inline :deep(.el-upload-dragger) {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--motion-fast), background var(--motion-fast);
  padding: 20px 32px;
  width: auto;
}

.training-upload-inline :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary-light);
  background: var(--color-primary-soft);
}

.training-upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.training-upload-select {
  min-width: 240px;
}

.training-control-panel :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.training-file-table {
  margin-top: 0;
}

/* training-workbench 现在只包含摘要区 */
.training-workbench {
  margin-bottom: var(--gap);
}

/* 摘要行：KPI + 风险提示横向排列 */
.training-summary-row {
  display: flex;
  align-items: stretch;
  gap: var(--gap);
  margin-bottom: var(--gap);
}

.training-kpi-strip {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.kpi-item {
  flex: 1;
  min-width: 0;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  text-align: center;
  animation: stagger-fade var(--motion-slow) var(--ease-emphasized) both;
}

.kpi-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
  margin-bottom: 4px;
}

.kpi-value {
  display: block;
  font-size: clamp(20px, 2.5vw, 28px);
  font-weight: 800;
  color: var(--color-ink);
}

.kpi-desc {
  display: block;
  font-size: 11px;
  color: var(--color-soft);
  margin-top: 4px;
}

.training-warning-inline {
  flex-shrink: 0;
  width: 300px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  overflow: auto;
}

/* 训练指标卡片 */
.training-metrics .metric-card {
  text-align: center;
}

.compact-metric span {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
  margin-bottom: 4px;
}

.compact-metric small {
  display: block;
  font-size: 11px;
  color: var(--color-soft);
  margin-top: 4px;
}

/* 图表面板 */
.chart-panel {
  transition: box-shadow var(--motion-fast);
}

.chart-panel:hover {
  box-shadow: var(--shadow-md);
}

/* AI 训练面板 */
.training-ai-panel {
  position: relative;
  overflow: hidden;
}

.training-ai-panel::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #2563eb, #7c3aed, #0891b2);
  opacity: 0.7;
}

.training-ai-answer {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid var(--color-border);
  padding: 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* 风险提示 */
.training-warning-list div {
  padding: 10px 14px;
  margin-bottom: 6px;
  border-radius: var(--radius-sm);
  background: #fffbeb;
  border: 1px solid #fde68a;
  font-size: 13px;
  color: #92400e;
  animation: slide-up-fade var(--motion-normal) var(--ease-emphasized) both;
}

@media (max-width: 1200px) {
  .training-summary-row {
    flex-direction: column;
  }
  .training-warning-inline {
    width: 100%;
  }
  .training-kpi-strip {
    flex-wrap: wrap;
  }
  .kpi-item {
    min-width: 140px;
  }
}
</style>