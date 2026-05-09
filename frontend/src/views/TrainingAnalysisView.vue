<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>训练分析报告</h1>
        <p>上传 YOLO results.csv，查看 Precision、Recall、mAP、Loss 曲线与 AI 诊断建议。</p>
      </div>
      <div class="ws-tags">
        <el-tag size="small" :type="summary ? 'success' : 'info'">{{ summary ? '已加载' : '等待 CSV' }}</el-tag>
        <el-tag size="small" :type="assistantStatus?.configured ? 'success' : 'warning'">{{ aiStatusText }}</el-tag>
      </div>
    </div>

    <div class="ws-panel-2-wide">
      <div class="ws-card">
        <div class="ws-card-header">训练数据</div>
        <div class="ws-card-body">
          <el-upload drag accept=".csv" :auto-upload="false" :limit="1" :on-change="selectCsv" :on-remove="removeCsv">
            <p>拖拽或选择 YOLO results.csv 文件</p>
          </el-upload>
          <div class="flex-gap mb" style="margin-top:8px">
            <el-button type="primary" size="small" :loading="uploading" :disabled="!csvFile || uploading" @click="uploadCsv">上传并分析</el-button>
            <el-button size="small" :loading="loadingFiles" @click="loadFiles">刷新列表</el-button>
          </div>
          <div class="flex-gap mb">
            <el-button size="small" :disabled="!summary" @click="exportReport">导出报告</el-button>
            <el-button size="small" type="danger" plain :disabled="!canManageTraining || !selectedName" @click="removeCurrentAnalysis">删除当前</el-button>
            <el-button size="small" type="danger" :disabled="!canManageTraining || !files.length" @click="clearAllAnalyses">清空全部</el-button>
          </div>
          <el-divider />
          <el-select v-model="selectedName" filterable placeholder="选择已上传 CSV" class="full" :loading="loadingFiles" @change="loadSummary">
            <el-option v-for="item in files" :key="item.name" :label="item.name" :value="item.name" />
          </el-select>
          <el-table v-loading="loadingFiles" :data="files" empty-text="暂无训练 CSV" @row-click="selectFileRow" style="margin-top:8px">
            <el-table-column prop="name" label="文件名" min-width="170" />
            <el-table-column prop="rows" label="Epoch" width="90" />
            <el-table-column prop="best_epoch" label="最佳" width="90" />
          </el-table>
        </div>
      </div>

      <div>
        <div class="ws-metrics-row cols-2" style="grid-template-columns:repeat(2, 1fr)">
          <div v-for="card in summaryCards" :key="card.label" class="ws-metric">
            <span class="m-label">{{ card.label }}</span>
            <span class="m-value" style="font-size:18px">{{ card.value }}</span>
            <span class="m-desc">{{ card.desc }}</span>
          </div>
        </div>
        <div class="ws-card">
          <div class="ws-card-header">风险提示</div>
          <div class="ws-card-body">
            <div v-if="summary?.warnings.length" class="ws-list">
              <div v-for="item in summary.warnings" :key="item" class="ws-list-item" style="border-left:3px solid var(--warning)">{{ item }}</div>
            </div>
            <el-empty v-else :description="summary ? '未发现明显风险' : '加载 CSV 后显示'" />
          </div>
        </div>
      </div>
    </div>

    <div class="ws-chart-grid" style="margin-top:14px">
      <div class="ws-chart-card"><div class="ws-card-header">Precision / Recall 曲线</div><div class="ws-card-body"><div ref="precisionRecallEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">mAP 曲线</div><div class="ws-card-body"><div ref="mapEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">训练 / 验证 Loss 曲线</div><div class="ws-card-body"><div ref="lossEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">最终指标雷达图</div><div class="ws-card-body"><div ref="radarEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">最终 Loss 柱状对比</div><div class="ws-card-body"><div ref="barEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">学习率曲线</div><div class="ws-card-body"><div ref="lrEl" v-loading="summaryLoading" class="ws-chart-box" style="height:200px"></div></div></div>
    </div>

    <div class="ws-card" style="margin-top:14px">
      <div class="ws-card-header">
        <span>AI 训练分析</span>
        <el-button type="primary" size="small" :loading="aiLoading" :disabled="!canUseAi" @click="generateAiReport">生成 AI 报告</el-button>
      </div>
      <div class="ws-card-body">
        <div class="mb"><el-tag size="small" :type="canUseAi ? 'success' : 'warning'">{{ aiActionText }}</el-tag></div>
        <div v-if="aiReport" class="analysis-card">{{ aiReport }}</div>
        <el-empty v-else description="点击生成后显示 AI 训练报告" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getAssistantStatus, type AssistantStatus } from '@/api/assistant'
import { clearTrainingAnalyses, deleteTrainingAnalysis, exportTrainingReport, getTrainingAiReport, getTrainingSummary, listTrainingFiles, uploadTrainingResults, type TrainingAnalysisFile, type TrainingAnalysisSummary } from '@/api/trainingAnalysis'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const files = ref<TrainingAnalysisFile[]>([])
const csvFile = ref<File | null>(null)
const selectedName = ref('')
const summary = ref<TrainingAnalysisSummary | null>(null)
const assistantStatus = ref<AssistantStatus | null>(null)
const aiReport = ref('')
const loadingFiles = ref(false); const uploading = ref(false); const summaryLoading = ref(false); const aiLoading = ref(false)
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
const aiStatusText = computed(() => { if (!auth.hasPermission('assistant:use')) return '无 AI 权限'; return assistantStatus.value?.configured ? `AI 已配置：${assistantStatus.value.model}` : 'AI 未配置' })
const aiActionText = computed(() => { if (!summary.value) return '请先加载训练摘要'; if (!auth.hasPermission('assistant:use')) return '无 AI 助手权限'; if (!assistantStatus.value?.configured) return '后端未配置 AI_ASSISTANT_API_KEY'; return '可生成训练分析报告' })

onMounted(async () => { window.addEventListener('resize', resizeCharts); await Promise.all([loadFiles(), loadAssistantStatus()]) })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); disposeCharts() })

function selectCsv(file: UploadFile) { const raw = file.raw || null; if (raw && !raw.name.toLowerCase().endsWith('.csv')) { ElMessage.warning('仅支持 CSV'); csvFile.value = null; return } csvFile.value = raw }
function removeCsv() { csvFile.value = null }
async function uploadCsv() { if (!csvFile.value) return; uploading.value = true; try { const data = await uploadTrainingResults(csvFile.value); selectedName.value = data.file.name; summary.value = data.summary; aiReport.value = ''; await loadFiles(false); await nextTick(); renderCharts(); ElMessage.success('CSV 已上传并解析') } finally { uploading.value = false } }
async function loadFiles(autoLoad = true) { loadingFiles.value = true; try { const data = await listTrainingFiles(); files.value = data.items; if (autoLoad && !summary.value && data.items.length) { selectedName.value = data.items[0].name; await loadSummary(selectedName.value) } } finally { loadingFiles.value = false } }
async function loadAssistantStatus() { if (!auth.hasPermission('assistant:use')) return; assistantStatus.value = await getAssistantStatus() }
async function loadSummary(name: string) { if (!name) return; summaryLoading.value = true; try { summary.value = await getTrainingSummary(name); selectedName.value = name; aiReport.value = ''; await nextTick(); renderCharts() } finally { summaryLoading.value = false } }
function selectFileRow(row: TrainingAnalysisFile) { loadSummary(row.name) }
async function generateAiReport() { if (!summary.value) return; aiLoading.value = true; try { const data = await getTrainingAiReport(summary.value.name, summary.value); aiReport.value = data.answer; ElMessage.success('AI 训练分析已生成') } finally { aiLoading.value = false } }
async function exportReport() { if (!summary.value) return; const response = await exportTrainingReport(summary.value.name); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = `${summary.value.name.replace(/\.csv$/i, '')}_training_report.txt`; link.click(); URL.revokeObjectURL(url); ElMessage.success('报告已导出') }
async function removeCurrentAnalysis() { if (!selectedName.value) return; try { await ElMessageBox.confirm(`确认删除 ${selectedName.value} 吗？`, '删除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; await deleteTrainingAnalysis(selectedName.value); summary.value = null; aiReport.value = ''; selectedName.value = ''; disposeCharts(); await loadFiles(); ElMessage.success('已删除') }
async function clearAllAnalyses() { if (!files.value.length) return; try { await ElMessageBox.confirm(`确认清空全部 ${files.value.length} 条训练分析吗？`, '清空确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; await clearTrainingAnalyses(); summary.value = null; aiReport.value = ''; selectedName.value = ''; files.value = []; disposeCharts(); ElMessage.success('已清空') }

function renderCharts() { disposeCharts(); if (!summary.value) return; renderPrecisionRecallChart(); renderMapChart(); renderLossChart(); renderRadarChart(); renderBarChart(); renderLearningRateChart() }
function makeChart(el: HTMLElement | null) { if (!el) return null; const chart = echarts.init(el, null, { backgroundColor: 'transparent' } as any); charts.push(chart); return chart }
function disposeCharts() { charts.forEach((chart) => chart.dispose()); charts = [] }
function resizeCharts() { charts.forEach((chart) => chart.resize()) }
function chartBaseGrid(top = 30) { return { left: 44, right: 20, top, bottom: 32 } }
function toEpochSeries(values: number[]) { const epochs = summary.value?.epochs || []; return epochs.map((epoch, index) => [epoch, values[index]]) }
function lineSeries(name: string, values: number[], extra: Record<string, unknown> = {}) { return { name, type: 'line', smooth: true, showSymbol: false, symbolSize: 5, connectNulls: true, lineStyle: { width: 2 }, emphasis: { focus: 'series' }, data: toEpochSeries(values), ...extra } }

function renderPrecisionRecallChart() { const chart = makeChart(precisionRecallEl.value); const data = summary.value; if (!chart || !data) return; chart.setOption({ color: ['#58a6ff', '#d29922'], tooltip: { trigger: 'axis' }, legend: { top: 2, textStyle: { color: '#8b949e', fontSize: 10 } }, grid: chartBaseGrid(30), xAxis: { type: 'value', name: 'Epoch', nameTextStyle: { color: '#8b949e' }, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', max: 1, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [lineSeries('Precision', data.precision), lineSeries('Recall', data.recall)] }) }
function renderMapChart() { const chart = makeChart(mapEl.value); const data = summary.value; if (!chart || !data) return; chart.setOption({ color: ['#58a6ff', '#3fb950'], tooltip: { trigger: 'axis' }, legend: { top: 2, textStyle: { color: '#8b949e', fontSize: 10 } }, grid: chartBaseGrid(30), xAxis: { type: 'value', name: 'Epoch', nameTextStyle: { color: '#8b949e' }, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', max: 1, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [lineSeries('mAP50', data.map50, { areaStyle: { opacity: 0.1 } }), lineSeries('mAP50-95', data.map5095, { areaStyle: { opacity: 0.06 } })] }) }
function renderLossChart() { const chart = makeChart(lossEl.value); const data = summary.value; if (!chart || !data) return; chart.setOption({ color: ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#8b949e', '#bc8cff'], tooltip: { trigger: 'axis' }, legend: { top: 2, type: 'scroll', textStyle: { color: '#8b949e', fontSize: 10 } }, grid: chartBaseGrid(36), xAxis: { type: 'value', name: 'Epoch', nameTextStyle: { color: '#8b949e' }, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [lineSeries('Train Box', data.train_box_loss), lineSeries('Train Cls', data.train_cls_loss), lineSeries('Train DFL', data.train_dfl_loss), lineSeries('Val Box', data.val_box_loss), lineSeries('Val Cls', data.val_cls_loss), lineSeries('Val DFL', data.val_dfl_loss)] }) }
function renderRadarChart() { const chart = makeChart(radarEl.value); const data = summary.value; if (!chart || !data) return; const values = data.radar.map((item) => Number(item.value) || 0); chart.setOption({ color: ['#58a6ff'], tooltip: {}, radar: { indicator: data.radar.map((item) => ({ name: String(item.name), max: 1 })), radius: '64%', axisName: { color: '#8b949e', fontSize: 10 } }, series: [{ type: 'radar', areaStyle: { opacity: 0.14 }, data: [{ name: '最终指标', value: values }] }] }) }
function renderBarChart() { const chart = makeChart(barEl.value); const data = summary.value; if (!chart || !data) return; chart.setOption({ color: ['#d29922'], tooltip: { trigger: 'axis' }, grid: { left: 110, right: 16, top: 10, bottom: 20 }, xAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, yAxis: { type: 'category', data: data.bar_metrics.map((item) => item.name), axisLabel: { color: '#8b949e' } }, series: [{ type: 'bar', barWidth: 18, data: data.bar_metrics.map((item) => Number(item.value) || 0) }] }) }
function renderLearningRateChart() { const chart = makeChart(lrEl.value); const data = summary.value; if (!chart || !data) return; chart.setOption({ color: ['#58a6ff', '#d29922', '#3fb950'], tooltip: { trigger: 'axis' }, legend: { top: 2, textStyle: { color: '#8b949e', fontSize: 10 } }, grid: chartBaseGrid(30), xAxis: { type: 'value', name: 'Epoch', nameTextStyle: { color: '#8b949e' }, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [lineSeries('lr/pg0', data.lr_pg0), lineSeries('lr/pg1', data.lr_pg1), lineSeries('lr/pg2', data.lr_pg2)] }) }
function formatRatio(value?: number | null) { if (value === null || value === undefined) return '-'; return `${(Number(value) * 100).toFixed(1)}%` }
</script>
