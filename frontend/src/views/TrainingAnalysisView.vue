<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>训练分析</h2>
        <p>上传 YOLO results.csv，查看训练曲线、最终指标和 AI 诊断</p>
      </div>
      <div style="display:flex;gap:8px">
        <el-tag :type="summary ? 'success' : 'info'" size="small">{{ summary ? '已加载' : '等待 CSV' }}</el-tag>
        <el-tag :type="assistantStatus?.configured ? 'success' : 'warning'" size="small">{{ aiStatusText }}</el-tag>
      </div>
    </div>

    <div class="training-layout">
      <div class="training-sidebar">
        <el-card shadow="never">
          <template #header>训练数据</template>
          <el-upload drag accept=".csv" :auto-upload="false" :limit="1" :on-change="selectCsv" :on-remove="removeCsv">
            <p>拖拽或选择 YOLO results.csv 文件</p>
          </el-upload>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">
            <el-button type="primary" :loading="uploading" :disabled="!csvFile || uploading" @click="uploadCsv">上传并分析</el-button>
            <el-button :loading="loadingFiles" @click="loadFiles">刷新列表</el-button>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px">
            <el-button :disabled="!summary" @click="exportReport">导出</el-button>
            <el-button type="danger" plain :disabled="!canManageTraining || !selectedName" @click="removeCurrentAnalysis">删除当前</el-button>
            <el-button type="danger" :disabled="!canManageTraining || !files.length" @click="clearAllAnalyses">清空全部</el-button>
          </div>
          <el-divider />
          <el-select v-model="selectedName" filterable placeholder="选择已上传 CSV" style="width:100%" :loading="loadingFiles" @change="loadSummary">
            <el-option v-for="item in files" :key="item.name" :label="item.name" :value="item.name" />
          </el-select>
          <div style="margin-top:10px">
            <el-table v-loading="loadingFiles" :data="files" empty-text="暂无训练 CSV" @row-click="selectFileRow" :show-header="true" size="small">
              <el-table-column prop="name" label="文件名" min-width="140" />
              <el-table-column prop="rows" label="Epoch" width="70" />
              <el-table-column prop="best_epoch" label="最佳" width="70" />
            </el-table>
          </div>
        </el-card>
      </div>

      <div>
        <div class="training-metrics">
          <div v-for="card in summaryCards" :key="card.label" class="stat-card">
            <div class="stat-label">{{ card.label }}</div>
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-desc">{{ card.desc }}</div>
          </div>
        </div>
        <el-card shadow="never">
          <template #header>风险提示</template>
          <div v-if="summary?.warnings.length">
            <div v-for="item in summary.warnings" :key="item" style="padding:8px 12px;border:1px solid #fde2b8;border-radius:4px;background:#fef7ed;margin-bottom:6px;font-size:13px;color:#b88230">{{ item }}</div>
          </div>
          <el-empty v-else :description="summary ? '未发现明显风险提示' : '加载 CSV 后显示风险提示'" :image-size="40" />
        </el-card>
      </div>
    </div>

    <div class="chart-grid" style="margin-top:16px">
      <el-card shadow="never"><template #header>Precision / Recall 曲线</template><div ref="precisionRecallEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
      <el-card shadow="never"><template #header>mAP 曲线</template><div ref="mapEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
      <el-card shadow="never"><template #header>训练 / 验证 Loss 曲线</template><div ref="lossEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
      <el-card shadow="never"><template #header>最终指标雷达图</template><div ref="radarEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
      <el-card shadow="never"><template #header>最终 Loss 柱状对比</template><div ref="barEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
      <el-card shadow="never"><template #header>学习率曲线</template><div ref="lrEl" v-loading="summaryLoading" class="chart-box"></div></el-card>
    </div>

    <el-card shadow="never" style="margin-top:16px">
      <template #header><div class="flex-between"><span>AI 训练分析</span><el-button type="primary" :loading="aiLoading" :disabled="!canUseAi" @click="generateAiReport">生成 AI 报告</el-button></div></template>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;font-size:13px">
        <el-tag :type="canUseAi ? 'success' : 'warning'" size="small">{{ aiActionText }}</el-tag>
        <span style="color:#909399">AI 会基于当前 summary 生成训练质量分析和优化建议。</span>
      </div>
      <div v-if="aiReport" style="padding:14px;background:#fafbfc;border:1px solid #e4e7ed;border-radius:4px;font-size:14px;line-height:1.8;white-space:pre-wrap">{{ aiReport }}</div>
      <el-empty v-else description="点击生成后显示 AI 训练报告" :image-size="40" />
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getAssistantStatus, type AssistantStatus } from '@/api/assistant'
import {
  clearTrainingAnalyses, deleteTrainingAnalysis, exportTrainingReport,
  getTrainingAiReport, getTrainingSummary, listTrainingFiles, uploadTrainingResults,
  type TrainingAnalysisFile, type TrainingAnalysisSummary,
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
  { label: '最佳 Epoch', value: summary.value?.best_epoch ?? '-', desc: '按 mAP50 峰值定位' },
  { label: '最佳 mAP50', value: formatRatio(summary.value?.best_map50), desc: '训练过程最高 mAP50' },
  { label: '最终 Recall', value: formatRatio(summary.value?.final_metrics.recall), desc: '最后一轮召回率' },
])
const canUseAi = computed(() => Boolean(summary.value && auth.hasPermission('assistant:use') && assistantStatus.value?.configured))
const canManageTraining = computed(() => auth.hasPermission('history:manage'))
const aiStatusText = computed(() => {
  if (!auth.hasPermission('assistant:use')) return '无 AI 权限'
  return assistantStatus.value?.configured ? `AI 已配置：${assistantStatus.value.model}` : 'AI 未配置'
})
const aiActionText = computed(() => {
  if (!summary.value) return '请先加载训练摘要'
  if (!auth.hasPermission('assistant:use')) return '无 AI 助手权限'
  if (!assistantStatus.value?.configured) return '后端未配置 AI_ASSISTANT_API_KEY'
  return '可生成训练分析报告'
})

onMounted(async () => { window.addEventListener('resize', resizeCharts); await Promise.all([loadFiles(), loadAssistantStatus()]) })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); disposeCharts() })

function selectCsv(file: UploadFile) {
  const raw = file.raw || null
  if (raw && !raw.name.toLowerCase().endsWith('.csv')) { ElMessage.warning('仅支持 CSV 文件'); csvFile.value = null; return }
  csvFile.value = raw
}
function removeCsv() { csvFile.value = null }
async function uploadCsv() {
  if (!csvFile.value) return
  uploading.value = true
  try { const data = await uploadTrainingResults(csvFile.value); selectedName.value = data.file.name; summary.value = data.summary; aiReport.value = ''; await loadFiles(false); await nextTick(); renderCharts(); ElMessage.success('训练 CSV 已上传并解析') }
  finally { uploading.value = false }
}
async function loadFiles(autoLoad = true) {
  loadingFiles.value = true
  try {
    const data = await listTrainingFiles(); files.value = data.items
    if (autoLoad && !summary.value && data.items.length) { selectedName.value = data.items[0].name; await loadSummary(selectedName.value) }
  } finally { loadingFiles.value = false }
}
async function loadAssistantStatus() { if (!auth.hasPermission('assistant:use')) return; assistantStatus.value = await getAssistantStatus() }
async function loadSummary(name: string) { if (!name) return; summaryLoading.value = true; try { summary.value = await getTrainingSummary(name); selectedName.value = name; aiReport.value = ''; await nextTick(); renderCharts() } finally { summaryLoading.value = false } }
function selectFileRow(row: TrainingAnalysisFile) { loadSummary(row.name) }
async function generateAiReport() { if (!summary.value) return; aiLoading.value = true; try { const data = await getTrainingAiReport(summary.value.name, summary.value); aiReport.value = data.answer; ElMessage.success('AI 训练分析已生成') } finally { aiLoading.value = false } }
async function exportReport() {
  if (!summary.value) return
  const response = await exportTrainingReport(summary.value.name); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = `${summary.value.name.replace(/\.csv$/i, '')}_training_report.txt`; link.click(); URL.revokeObjectURL(url); ElMessage.success('训练分析报告已导出')
}
async function removeCurrentAnalysis() {
  if (!selectedName.value) return
  try { await ElMessageBox.confirm(`确认删除当前训练分析 ${selectedName.value} 吗？`, '删除当前分析', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }
  await deleteTrainingAnalysis(selectedName.value); ElMessage.success('当前训练分析已删除'); summary.value = null; aiReport.value = ''; selectedName.value = ''; disposeCharts(); await loadFiles()
}
async function clearAllAnalyses() {
  if (!files.value.length) return
  try { await ElMessageBox.confirm(`确认清空全部 ${files.value.length} 条训练分析吗？`, '清空全部分析', { type: 'warning', confirmButtonText: '确认清空', cancelButtonText: '取消' }) } catch { return }
  await clearTrainingAnalyses(); ElMessage.success('全部训练分析已清空'); summary.value = null; aiReport.value = ''; selectedName.value = ''; files.value = []; disposeCharts()
}
function renderCharts() { disposeCharts(); if (!summary.value) return; renderPrecisionRecallChart(); renderMapChart(); renderLossChart(); renderRadarChart(); renderBarChart(); renderLearningRateChart() }
function makeChart(el: HTMLElement | null) { if (!el) return null; const chart = echarts.init(el); charts.push(chart); return chart }
function disposeCharts() { charts.forEach((chart) => chart.dispose()); charts = [] }
function resizeCharts() { charts.forEach((chart) => chart.resize()) }
function chartBaseGrid(top = 34) { return { left: 48, right: 24, top, bottom: 38 } }
function toEpochSeries(values: number[]) { const epochs = summary.value?.epochs || []; return epochs.map((epoch, index) => [epoch, values[index]]) }
function lineSeries(name: string, values: number[], extra: Record<string, unknown> = {}) { return { name, type: 'line', smooth: true, showSymbol: false, symbol: 'circle', symbolSize: 5, connectNulls: true, lineStyle: { width: 3 }, emphasis: { focus: 'series' }, data: toEpochSeries(values), ...extra } }
function renderPrecisionRecallChart() {
  const chart = makeChart(precisionRecallEl.value); const data = summary.value; if (!chart || !data) return
  chart.setOption({ color: ['#409eff', '#e6a23c'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value', max: 1 }, series: [lineSeries('Precision', data.precision), lineSeries('Recall', data.recall)] })
}
function renderMapChart() {
  const chart = makeChart(mapEl.value); const data = summary.value; if (!chart || !data) return
  chart.setOption({ color: ['#409eff', '#e6a23c'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value', max: 1 }, series: [lineSeries('mAP50', data.map50, { areaStyle: { opacity: 0.12 } }), lineSeries('mAP50-95', data.map5095, { areaStyle: { opacity: 0.08 } })] })
}
function renderLossChart() {
  const chart = makeChart(lossEl.value); const data = summary.value; if (!chart || !data) return
  chart.setOption({ color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb'], tooltip: { trigger: 'axis' }, legend: { top: 0, type: 'scroll' }, grid: chartBaseGrid(54), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value' }, series: [lineSeries('Train Box', data.train_box_loss), lineSeries('Train Cls', data.train_cls_loss), lineSeries('Train DFL', data.train_dfl_loss), lineSeries('Val Box', data.val_box_loss), lineSeries('Val Cls', data.val_cls_loss), lineSeries('Val DFL', data.val_dfl_loss)] })
}
function renderRadarChart() {
  const chart = makeChart(radarEl.value); const data = summary.value; if (!chart || !data) return
  const values = data.radar.map((item) => Number(item.value) || 0)
  chart.setOption({ color: ['#409eff'], tooltip: {}, radar: { indicator: data.radar.map((item) => ({ name: String(item.name), max: 1 })), radius: '66%' }, series: [{ type: 'radar', areaStyle: { opacity: 0.18 }, data: [{ name: '最终指标', value: values }] }] })
}
function renderBarChart() {
  const chart = makeChart(barEl.value); const data = summary.value; if (!chart || !data) return
  chart.setOption({ color: ['#409eff'], tooltip: { trigger: 'axis' }, grid: { left: 112, right: 18, top: 20, bottom: 28 }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: data.bar_metrics.map((item) => item.name) }, series: [{ type: 'bar', barWidth: 20, data: data.bar_metrics.map((item) => Number(item.value) || 0) }] })
}
function renderLearningRateChart() {
  const chart = makeChart(lrEl.value); const data = summary.value; if (!chart || !data) return
  chart.setOption({ color: ['#409eff', '#e6a23c', '#67c23a'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value' }, series: [lineSeries('lr/pg0', data.lr_pg0), lineSeries('lr/pg1', data.lr_pg1), lineSeries('lr/pg2', data.lr_pg2)] })
}
function formatRatio(value?: number | null) { if (value === null || value === undefined) return '-'; return `${(Number(value) * 100).toFixed(1)}%` }
</script>
