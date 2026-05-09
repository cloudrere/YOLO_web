<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <span class="eyebrow dark">工作站首页</span>
        <h2>系统运行概览</h2>
        <p>集中展示当前模型、检测趋势、系统资源状态和快捷入口。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">刷新数据</el-button>
    </section>

    <section class="grid metrics">
      <div v-for="card in cards" :key="card.label" class="metric-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.desc }}</small>
      </div>
    </section>

    <section v-if="metrics?.admin" class="grid four" style="margin-bottom: var(--gap);">
      <div v-for="card in adminCards" :key="card.label" class="metric-card compact-metric">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.desc }}</small>
      </div>
    </section>

    <section v-if="metrics?.admin" class="grid two">
      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">系统资源快照</span></template>
        <div class="system-status-list">
          <div><span>CPU 使用率</span><strong>{{ formatPercent(system?.cpu_percent) }}</strong></div>
          <div><span>内存使用率</span><strong>{{ formatPercent(system?.memory?.percent) }}</strong></div>
          <div><span>可用内存</span><strong>{{ formatBytes(system?.memory?.available) }}</strong></div>
          <div><span>GPU 温度</span><strong>{{ system?.gpu_devices?.[0]?.temperature != null ? system.gpu_devices[0].temperature + '°C' : '不可用' }}</strong></div>
        </div>
        <div ref="resourceEl" class="mini-chart" style="margin-top: 14px;"></div>
      </el-card>
      <el-card class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">GPU / CUDA 诊断</span></template>
        <div class="gpu-diagnostic-list">
          <div v-for="check in system?.diagnostics.checks || []" :key="check.name" class="diagnostic-row">
            <el-tag :type="diagnosticTag(check.status)" size="small">{{ check.name }}</el-tag>
            <span>{{ check.message }}</span>
          </div>
        </div>
        <div v-if="system?.gpu_devices.length" class="gpu-list">
          <div v-for="gpu in system.gpu_devices" :key="gpu.index" class="gpu-card">
            <strong>{{ gpu.name }}</strong>
            <span>显存：{{ formatBytes(gpu.allocated_memory) }} / {{ formatBytes(gpu.total_memory) }}</span>
            <span>温度：{{ gpu.temperature ?? '不可用' }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无可用 GPU 信息" />
      </el-card>
    </section>

    <section class="grid two" style="margin-bottom: var(--gap);">
      <el-card v-for="chartCard in chartCards" :key="chartCard.key" class="workstation-panel" shadow="never">
        <template #header><span style="font-weight: 700;">{{ chartCard.title }}</span></template>
        <div :ref="(el: any) => setChartRef(chartCard.key, el)" class="chart"></div>
      </el-card>
    </section>

    <el-card class="workstation-panel" shadow="never" style="margin-bottom: var(--gap);">
      <template #header><span style="font-weight: 700;">高频检测类别</span></template>
      <div class="top-class-list">
        <div v-for="item in metrics?.top_detected_classes || []" :key="item.class">
          <span>{{ item.class_zh || item.class }}</span>
          <strong>{{ item.count }}</strong>
        </div>
      </div>
      <el-empty v-if="!metrics?.top_detected_classes.length" description="暂无类别统计" />
    </el-card>

    <el-card v-if="metrics?.admin" class="workstation-panel" shadow="never">
      <template #header><span style="font-weight: 700;">用户检测统计</span></template>
      <div class="table-scroll">
        <el-table :data="metrics.admin.user_detection_stats" empty-text="暂无用户检测统计">
          <el-table-column prop="user_id" label="用户ID" width="100" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="count" label="检测次数" width="130" />
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getDashboardMetrics, type DashboardMetrics } from '@/api/dashboard'

const metrics = ref<DashboardMetrics | null>(null)
const loading = ref(false)
const chartRefs: Record<string, HTMLElement | null> = {}
const resourceEl = ref<HTMLElement | null>(null)
const resourceSamples = ref<Array<{ time: string; cpu: number; memory: number; gpu: number }>>([])
let charts: echarts.ECharts[] = []
let timer: number | undefined

function setChartRef(key: string, el: any) { chartRefs[key] = el as HTMLElement | null }

const chartCards = computed(() => [
  { key: 'trend', title: '近 7 日检测趋势' },
  { key: 'userTrend', title: '用户检测趋势' },
  { key: 'class', title: '类别分布' },
  { key: 'model', title: '模型调用排行' },
  { key: 'ai', title: 'AI 调用趋势' },
])

const system = computed(() => metrics.value?.admin?.system_status || null)
const cards = computed(() => [
  { label: '检测记录总数', value: metrics.value?.total_detections ?? 0, desc: '累计完成的检测记录' },
  { label: '图片检测', value: metrics.value?.image_count ?? 0, desc: '单图与批量图片' },
  { label: '视频检测', value: metrics.value?.video_count ?? 0, desc: '异步视频任务' },
  { label: '活跃用户', value: metrics.value?.active_users ?? 0, desc: '可登录账号数' },
])
const adminCards = computed(() => [
  { label: '总用户数', value: metrics.value?.admin?.total_users ?? 0, desc: '平台账号总数' },
  { label: '模型总数', value: metrics.value?.admin?.total_models ?? 0, desc: '未删除模型数量' },
  { label: '异常日志数', value: metrics.value?.admin?.abnormal_logs ?? 0, desc: '警告、错误和严重日志' },
  { label: 'AI 调用次数', value: metrics.value?.admin?.ai_call_count ?? 0, desc: 'AI 助手累计调用' },
])

onMounted(async () => { await load(); timer = window.setInterval(load, 15000) })
onBeforeUnmount(() => { window.clearInterval(timer); charts.forEach((c) => c.dispose()) })

async function load() {
  loading.value = true
  try {
    metrics.value = await getDashboardMetrics()
    collectResourceSample()
    await nextTick()
    renderCharts()
  } finally { loading.value = false }
}
function collectResourceSample() {
  if (!system.value) return
  const gpu = system.value.gpu_devices[0]
  resourceSamples.value.push({
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    cpu: Number(system.value.cpu_percent || 0),
    memory: Number(system.value.memory?.percent || 0),
    gpu: gpu ? Math.round((gpu.reserved_memory / Math.max(1, gpu.total_memory)) * 100) : 0,
  })
  resourceSamples.value = resourceSamples.value.slice(-12)
}
function makeChart(el: HTMLElement | null) {
  if (!el) return null
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}
function renderCharts() {
  charts.forEach((c) => c.dispose()); charts = []
  if (!metrics.value) return
  const m = metrics.value
  const trendChart = makeChart(chartRefs['trend'])
  if (trendChart) trendChart.setOption({
    color: ['#3366cc'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: m.daily_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.12 }, data: m.daily_trend_7d.map((item) => item.count) }],
  })
  const userChart = makeChart(chartRefs['userTrend'])
  if (userChart) {
    const users = Array.from(new Set(m.user_detection_trend_7d.flatMap((item) => Object.keys(item.users))))
    userChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, type: 'scroll' },
      grid: { left: 36, right: 16, top: 48, bottom: 28 },
      xAxis: { type: 'category', data: m.user_detection_trend_7d.map((item) => item.date.slice(5)) },
      yAxis: { type: 'value' },
      series: users.map((name) => ({ name, type: 'line', smooth: true, data: m.user_detection_trend_7d.map((item) => item.users[name] || 0) })),
    })
  }
  const classChart = makeChart(chartRefs['class'])
  if (classChart) classChart.setOption({
    color: ['#e89440'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 48 },
    xAxis: { type: 'category', data: m.class_distribution.map((item) => item.class_zh || item.class), axisLabel: { rotate: 25 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', barWidth: 24, data: m.class_distribution.map((item) => item.count) }],
  })
  const modelChart = makeChart(chartRefs['model'])
  if (modelChart) modelChart.setOption({
    color: ['#3366cc'],
    tooltip: { trigger: 'axis' },
    grid: { left: 92, right: 18, top: 24, bottom: 24 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: m.model_call_ranking.map((item) => item.model || '未命名') },
    series: [{ type: 'bar', data: m.model_call_ranking.map((item) => item.count) }],
  })
  const aiChart = makeChart(chartRefs['ai'])
  if (aiChart) aiChart.setOption({
    color: ['#c98826'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: m.ai_call_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.12 }, data: m.ai_call_trend_7d.map((item) => item.count) }],
  })
  const resChart = makeChart(resourceEl.value)
  if (resChart) resChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 36, right: 14, top: 44, bottom: 26 },
    xAxis: { type: 'category', data: resourceSamples.value.map((item) => item.time) },
    yAxis: { type: 'value', max: 100 },
    series: [
      { name: 'CPU', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.cpu) },
      { name: '内存', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.memory) },
      { name: 'GPU显存', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.gpu) },
    ],
  })
}
function diagnosticTag(status: string) {
  if (status === 'ok') return 'success'
  if (status === 'warning') return 'warning'
  if (status === 'error') return 'danger'
  return 'info'
}
function formatPercent(value?: number | null) { return value === null || value === undefined ? '不可用' : `${Number(value).toFixed(1)}%` }
function formatBytes(value?: number | null) {
  if (!value) return '不可用'
  if (value >= 1024 ** 3) return `${(value / 1024 ** 3).toFixed(1)} GB`
  if (value >= 1024 ** 2) return `${(value / 1024 ** 2).toFixed(1)} MB`
  return `${value} B`
}
</script>
