<template>
  <AppLayout>
    <!-- Hero -->
    <section class="workstation-hero">
      <div>
        <h2>训练实验室</h2>
        <p>上传 YOLO results.csv，查看 Precision、Recall、mAP、Loss 曲线与 AI 诊断建议。</p>
      </div>
      <div class="status-pills">
        <el-tag :type="summary ? 'success' : 'info'">{{ summary ? '已加载' : '等待 CSV' }}</el-tag>
        <el-tag :type="assistantStatus?.configured ? 'success' : 'warning'">{{ aiStatusText }}</el-tag>
      </div>
    </section>

    <!-- 双栏：文件列表 + 摘要 -->
    <section class="grid two" style="margin-bottom:var(--gap);">
      <!-- 左栏：文件管理 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">训练数据文件</span></template>
        <el-upload drag accept=".csv" :auto-upload="false" :limit="1" :on-change="selectCsv" :on-remove="removeCsv">
          <p style="font-size:13px;color:var(--color-muted);">拖拽或选择 YOLO results.csv</p>
        </el-upload>
        <div style="display:flex;gap:8px;margin-top:12px;">
          <el-button type="primary" size="small" :loading="uploading" :disabled="!csvFile || uploading" @click="uploadCsv">上传并分析</el-button>
          <el-button size="small" :loading="loadingFiles" @click="loadFiles">刷新列表</el-button>
        </div>
        <div style="display:flex;gap:8px;margin-top:8px;">
          <el-button size="small" :disabled="!summary" @click="exportReport">导出报告</el-button>
          <el-button size="small" type="danger" plain :disabled="!canManageTraining || !selectedName" @click="removeCurrentAnalysis">删除当前</el-button>
          <el-button size="small" type="danger" :disabled="!canManageTraining || !files.length" @click="clearAllAnalyses">清空全部</el-button>
        </div>
        <el-divider />
        <el-select v-model="selectedName" filterable placeholder="选择已上传 CSV" class="full" :loading="loadingFiles" @change="loadSummary">
          <el-option v-for="item in files" :key="item.name" :label="item.name" :value="item.name" />
        </el-select>
        <div class="table-scroll" style="margin-top:10px;">
          <el-table v-loading="loadingFiles" :data="files" empty-text="暂无训练文件" @row-click="selectFileRow" size="small">
            <el-table-column prop="name" label="文件名" min-width="170" />
            <el-table-column prop="rows" label="Epoch" width="80" />
            <el-table-column prop="best_epoch" label="最佳" width="80" />
          </el-table>
        </div>
      </el-card>

      <!-- 右栏：摘要 + 风险 -->
      <div style="display:grid;gap:var(--gap);">
        <div class="grid four" style="margin-bottom:0;">
          <div v-for="card in summaryCards" :key="card.label" class="metric-card">
            <span class="metric-label">{{ card.label }}</span>
            <span class="metric-value">{{ card.value }}</span>
            <span class="metric-desc">{{ card.desc }}</span>
          </div>
        </div>
        <el-card shadow="never">
          <template #header><span style="font-weight:700;">训练风险提示</span></template>
          <div v-if="summary?.warnings.length">
            <div v-for="item in summary.warnings" :key="item" style="padding:10px;border-radius:6px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;font-size:13px;margin-bottom:6px;">{{ item }}</div>
          </div>
          <el-empty v-else :description="summary ? '未发现明显风险' : '加载 CSV 后显示'" />
        </el-card>
      </div>
    </section>

    <!-- 训练曲线 6 图 -->
    <section class="grid two" style="margin-bottom:var(--gap);">
      <TrainingChartPanel :title="'Precision / Recall 曲线'" :option="chartOptions.pr" :watch-key="renderKey" />
      <TrainingChartPanel :title="'mAP 曲线'" :option="chartOptions.map" :watch-key="renderKey" />
      <TrainingChartPanel :title="'Loss 曲线'" :option="chartOptions.loss" :watch-key="renderKey" />
      <TrainingChartPanel :title="'最终指标雷达图'" :option="chartOptions.radar" :watch-key="renderKey" />
      <TrainingChartPanel :title="'Loss 柱状对比'" :option="chartOptions.bar" :watch-key="renderKey" />
      <TrainingChartPanel :title="'学习率曲线'" :option="chartOptions.lr" :watch-key="renderKey" />
    </section>

    <!-- AI 分析 -->
    <el-card shadow="never" style="margin-bottom:var(--gap);">
      <template #header>
        <div class="flex-between">
          <span style="font-weight:700;">AI 训练分析</span>
          <el-button type="primary" size="small" :loading="aiLoading" :disabled="!canUseAi" @click="generateAiReport">生成 AI 报告</el-button>
        </div>
      </template>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <el-tag :type="canUseAi ? 'success' : 'warning'" size="small">{{ aiActionText }}</el-tag>
        <span style="font-size:13px;color:var(--color-muted);">AI 会基于训练指标生成质量分析、风险判断和下一步优化建议。</span>
      </div>
      <div v-if="aiReport" style="min-height:200px;padding:16px;border-radius:var(--radius-md);background:var(--color-bg);border:1px solid var(--color-border);line-height:1.8;white-space:pre-wrap;">{{ aiReport }}</div>
      <el-empty v-else description="点击生成后显示 AI 训练报告" />
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import TrainingChartPanel from '@/components/detection/TrainingChartPanel.vue'
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
const loadingFiles = ref(false)
const uploading = ref(false)
const aiLoading = ref(false)
const renderKey = ref(0)

const summaryCards = computed(() => [
  { label: '总 Epoch', value: summary.value?.epochs.length ?? 0, desc: summary.value?.name || '上传 results.csv 后解析' },
  { label: '最佳 Epoch', value: summary.value?.best_epoch ?? '-', desc: '按 mAP50 峰值定位' },
  { label: '最佳 mAP50', value: formatRatio(summary.value?.best_map50), desc: '训练过程最高 mAP50' },
  { label: '最终 Recall', value: formatRatio(summary.value?.final_metrics.recall), desc: '最后一轮召回率' },
])
const canUseAi = computed(() => Boolean(summary.value && auth.hasPermission('assistant:use') && assistantStatus.value?.configured))
const canManageTraining = computed(() => auth.hasPermission('history:manage'))
const aiStatusText = computed(() => auth.hasPermission('assistant:use') ? (assistantStatus.value?.configured ? `AI: ${assistantStatus.value.model}` : 'AI 未配置') : '无 AI 权限')
const aiActionText = computed(() => {
  if (!summary.value) return '请先加载训练摘要'
  if (!auth.hasPermission('assistant:use')) return '无 AI 助手权限'
  if (!assistantStatus.value?.configured) return '后端未配置 AI_ASSISTANT_API_KEY'
  return '可生成训练分析报告'
})

function chartBaseGrid(top = 34) { return { left: 48, right: 24, top, bottom: 38 } }
function toEpochSeries(values: number[]) { return (summary.value?.epochs || []).map((epoch, i) => [epoch, values[i]]) }
function lineSeries(name: string, values: number[], extra: Record<string, unknown> = {}): Record<string, unknown> {
  return { name, type: 'line', smooth: true, showSymbol: false, symbol: 'circle', symbolSize: 5, connectNulls: true, lineStyle: { width: 3 }, emphasis: { focus: 'series' }, data: toEpochSeries(values), ...extra }
}

const chartOptions = ref<Record<string, Record<string, unknown>>>({
  pr: {},
  map: {},
  loss: {},
  radar: {},
  bar: {},
  lr: {},
})

function buildChartOptions() {
  const d = summary.value; if (!d) return
  const opts = chartOptions.value
  opts.pr = { color: ['#2563eb', '#ea580c'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value', max: 1 }, series: [lineSeries('Precision', d.precision), lineSeries('Recall', d.recall)] }
  opts.map = { color: ['#16a34a', '#d97706'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value', max: 1 }, series: [lineSeries('mAP50', d.map50, { areaStyle: { opacity: 0.1 } }), lineSeries('mAP50-95', d.map5095, { areaStyle: { opacity: 0.06 } })] }
  opts.loss = { color: ['#2563eb', '#0891b2', '#16a34a', '#ea580c', '#dc2626', '#8b5cf6'], tooltip: { trigger: 'axis' }, legend: { top: 0, type: 'scroll' }, grid: chartBaseGrid(54), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value' }, series: [lineSeries('Train Box', d.train_box_loss), lineSeries('Train Cls', d.train_cls_loss), lineSeries('Train DFL', d.train_dfl_loss), lineSeries('Val Box', d.val_box_loss), lineSeries('Val Cls', d.val_cls_loss), lineSeries('Val DFL', d.val_dfl_loss)] }
  const radarValues = d.radar.map((item) => Number(item.value) || 0)
  opts.radar = { color: ['#2563eb'], tooltip: {}, radar: { indicator: d.radar.map((item) => ({ name: String(item.name), max: 1 })), radius: '64%' }, series: [{ type: 'radar', areaStyle: { opacity: 0.14 }, data: [{ name: '最终指标', value: radarValues }] }] }
  opts.bar = { color: ['#ea580c'], tooltip: { trigger: 'axis' }, grid: { left: 112, right: 18, top: 20, bottom: 28 }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: d.bar_metrics.map((item) => item.name) }, series: [{ type: 'bar', barWidth: 18, data: d.bar_metrics.map((item) => Number(item.value) || 0) }] }
  opts.lr = { color: ['#2563eb', '#ea580c', '#0891b2'], tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: chartBaseGrid(46), xAxis: { type: 'value', name: 'Epoch', min: 'dataMin', max: 'dataMax' }, yAxis: { type: 'value' }, series: [lineSeries('lr/pg0', d.lr_pg0), lineSeries('lr/pg1', d.lr_pg1), lineSeries('lr/pg2', d.lr_pg2)] }
}

onMounted(async () => { await Promise.all([loadFiles(), loadAssistantStatus()]) })

function selectCsv(file: UploadFile) { const raw = file.raw || null; if (raw && !raw.name.toLowerCase().endsWith('.csv')) { ElMessage.warning('仅支持 CSV 文件'); csvFile.value = null; return }; csvFile.value = raw }
function removeCsv() { csvFile.value = null }
async function uploadCsv() { if (!csvFile.value) return; uploading.value = true; try { const data = await uploadTrainingResults(csvFile.value); selectedName.value = data.file.name; summary.value = data.summary; aiReport.value = ''; await loadFiles(false); buildChartOptions(); renderKey.value++; ElMessage.success('CSV 已上传解析') } finally { uploading.value = false } }
async function loadFiles(autoLoad = true) { loadingFiles.value = true; try { const data = await listTrainingFiles(); files.value = data.items; if (autoLoad && !summary.value && data.items.length) { selectedName.value = data.items[0].name; await loadSummary(selectedName.value) } } finally { loadingFiles.value = false } }
async function loadAssistantStatus() { if (auth.hasPermission('assistant:use')) assistantStatus.value = await getAssistantStatus() }
async function loadSummary(name: string) { if (!name) return; try { summary.value = await getTrainingSummary(name); selectedName.value = name; aiReport.value = ''; buildChartOptions(); renderKey.value++ } finally { } }
function selectFileRow(row: TrainingAnalysisFile) { loadSummary(row.name) }
async function generateAiReport() { if (!summary.value) return; aiLoading.value = true; try { const data = await getTrainingAiReport(summary.value.name, summary.value); aiReport.value = data.answer; ElMessage.success('AI 分析已生成') } finally { aiLoading.value = false } }
async function exportReport() { if (!summary.value) return; const response = await exportTrainingReport(summary.value.name); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = `${summary.value.name.replace(/\.csv$/i, '')}_training_report.txt`; link.click(); URL.revokeObjectURL(url); ElMessage.success('报告已导出') }
async function removeCurrentAnalysis() { if (!selectedName.value) return; try { await ElMessageBox.confirm(`确认删除 ${selectedName.value} ？`, '删除当前分析', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteTrainingAnalysis(selectedName.value); ElMessage.success('已删除'); summary.value = null; aiReport.value = ''; selectedName.value = ''; renderKey.value++; await loadFiles() }
async function clearAllAnalyses() { if (!files.value.length) return; try { await ElMessageBox.confirm(`确认清空全部 ${files.value.length} 条训练分析？`, '清空全部分析', { type: 'warning', confirmButtonText: '确认清空', cancelButtonText: '取消' }) } catch { return }; await clearTrainingAnalyses(); ElMessage.success('已清空'); summary.value = null; aiReport.value = ''; selectedName.value = ''; files.value = []; renderKey.value++ }
function formatRatio(value?: number | null) { if (value === null || value === undefined) return '-'; return `${(Number(value) * 100).toFixed(1)}%` }
</script>
