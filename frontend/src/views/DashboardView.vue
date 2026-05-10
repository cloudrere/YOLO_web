<template>
  <AppLayout>
    <AnimatedPage>
      <!-- Hero 横幅 -->
      <section class="workstation-hero">
        <div class="hero-info">
          <span class="hero-eyebrow">动态检测指挥台</span>
          <h2>实时态势总览</h2>
          <p>
            <template v-if="system">
              <span class="hero-stat">
                <StatusPulse :status="system.gpu_devices?.length ? 'success' : 'warning'" size="sm" />
                GPU: {{ system.gpu_devices?.[0]?.name || '未检测到' }}
              </span>
              <span class="hero-sep">|</span>
              <span class="hero-stat">
                <StatusPulse :status="system.diagnostics?.checks?.every((c: any) => c.status === 'ok') ? 'success' : 'warning'" size="sm" />
                CUDA: {{ system.diagnostics?.checks?.every((c: any) => c.status === 'ok') ? '就绪' : '异常' }}
              </span>
            </template>
            <template v-else>
              <span class="hero-stat">
                <StatusPulse status="idle" size="sm" />
                系统状态加载中...
              </span>
            </template>
          </p>
        </div>
        <div class="hero-actions">
          <el-button type="primary" size="large" :loading="loading" @click="load">刷新数据</el-button>
        </div>
      </section>

      <!-- 核心 KPI 卡片 -->
      <section class="grid four stagger-container">
        <div class="metric-card">
          <span class="metric-label">今日检测</span>
          <span class="metric-value">
            <AnimatedNumber :value="metrics?.daily_trend_7d?.length ? (metrics.daily_trend_7d[metrics.daily_trend_7d.length - 1]?.count ?? 0) : 0" :duration="1000" />
          </span>
          <span class="metric-desc">当日完成检测任务</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">活跃模型</span>
          <span class="metric-value">
            <AnimatedNumber :value="metrics?.admin?.total_models ?? 0" :duration="1000" />
          </span>
          <span class="metric-desc">已登记模型总数</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">GPU 显存占用</span>
          <span class="metric-value">
            <AnimatedNumber :value="system?.gpu_devices?.[0] ? Math.round((system.gpu_devices[0].reserved_memory / Math.max(1, system.gpu_devices[0].total_memory)) * 100) : 0" :duration="1000" />
            <small class="metric-unit">%</small>
          </span>
          <span class="metric-desc">{{ system?.gpu_devices?.[0]?.name || '无可用 GPU' }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">系统健康</span>
          <span class="metric-value">
            <AnimatedNumber :value="system?.diagnostics?.checks?.filter((c: any) => c.status === 'ok').length ?? 0" :duration="1000" />
            <small class="metric-unit">/ {{ system?.diagnostics?.checks?.length || 0 }}</small>
          </span>
          <span class="metric-desc">诊断检查通过项</span>
        </div>
      </section>

      <!-- 次要指标卡片 -->
      <section class="grid four stagger-container">
        <div v-for="card in cards" :key="card.label" class="metric-card">
          <span class="metric-label">{{ card.label }}</span>
          <span class="metric-value">
            <AnimatedNumber :value="Number(card.value)" :duration="800" />
          </span>
          <span class="metric-desc">{{ card.desc }}</span>
        </div>
      </section>

      <!-- 管理员指标 -->
      <section v-if="metrics?.admin" class="grid four stagger-container">
        <div v-for="card in adminCards" :key="card.label" class="metric-card">
          <span class="metric-label">{{ card.label }}</span>
          <span class="metric-value">
            <AnimatedNumber :value="Number(card.value)" :duration="800" />
          </span>
          <span class="metric-desc">{{ card.desc }}</span>
        </div>
      </section>

      <!-- GPU / CUDA 诊断双栏 -->
      <section v-if="metrics?.admin" class="grid two">
        <el-card shadow="never">
          <template #header>
            <div class="card-header-row">
              <span>系统资源快照</span>
              <StatusPulse status="running" size="sm" />
            </div>
          </template>
          <div class="health-list">
            <div class="health-status-line">
              <span>CPU 使用率</span>
              <strong>{{ formatPercent(system?.cpu_percent) }}</strong>
            </div>
            <div class="health-status-line">
              <span>内存使用率</span>
              <strong>{{ formatPercent(system?.memory?.percent) }}</strong>
            </div>
            <div class="health-status-line">
              <span>可用内存</span>
              <strong>{{ formatBytes(system?.memory?.available) }}</strong>
            </div>
            <div class="health-status-line">
              <span>GPU 温度</span>
              <strong>{{ system?.gpu_devices?.[0]?.temperature != null ? system.gpu_devices[0].temperature + '°C' : '不可用' }}</strong>
            </div>
          </div>
          <div ref="resourceEl" class="chart mini-chart"></div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <div class="card-header-row">
              <span>GPU / CUDA 诊断</span>
              <StatusPulse :status="system?.diagnostics?.checks?.every((c: any) => c.status === 'ok') ? 'success' : 'danger'" size="sm" />
            </div>
          </template>
          <div class="health-list">
            <div v-for="check in system?.diagnostics?.checks || []" :key="check.name" class="health-status-line">
              <el-tag :type="diagnosticTag(check.status)" size="small">{{ check.name }}</el-tag>
              <span class="diag-msg">{{ check.message }}</span>
            </div>
            <el-empty v-if="!system?.diagnostics?.checks?.length" description="暂无诊断数据" :image-size="48" />
          </div>
          <div v-if="system?.gpu_devices?.length" class="gpu-device-list">
            <div v-for="gpu in system.gpu_devices" :key="gpu.index" class="gpu-device-card">
              <strong>{{ gpu.name }}</strong>
              <div class="gpu-stats">
                <span>显存 {{ formatBytes(gpu.allocated_memory) }} / {{ formatBytes(gpu.total_memory) }}</span>
                <span>温度 {{ gpu.temperature ?? 'N/A' }}°C</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无可用 GPU 信息" :image-size="48" />
        </el-card>
      </section>

      <!-- ECharts 图表区 -->
      <section class="grid two">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">近 7 日检测趋势</span>
          </template>
          <div ref="trendEl" class="chart"></div>
        </el-card>
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">用户检测趋势</span>
          </template>
          <div ref="userTrendEl" class="chart"></div>
        </el-card>
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">类别分布</span>
          </template>
          <div ref="classEl" class="chart"></div>
        </el-card>
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">模型调用排行</span>
          </template>
          <div ref="modelEl" class="chart"></div>
        </el-card>
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">AI 调用趋势</span>
          </template>
          <div ref="aiEl" class="chart"></div>
        </el-card>
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">高频检测类别</span>
          </template>
          <div class="top-class-list">
            <TransitionGroup name="list">
              <div v-for="item in metrics?.top_detected_classes || []" :key="item.class" class="top-class-item">
                <span class="class-name">{{ item.class_zh || item.class }}</span>
                <div class="class-bar-wrap">
                  <div class="class-bar" :style="{ width: Math.round((item.count / Math.max(1, (metrics?.top_detected_classes || [])[0]?.count || 1)) * 100) + '%' }"></div>
                </div>
                <strong class="class-count">{{ item.count }}</strong>
              </div>
            </TransitionGroup>
          </div>
          <el-empty v-if="!metrics?.top_detected_classes?.length" description="暂无类别统计" :image-size="48" />
        </el-card>
      </section>

      <!-- 检测任务时间线 -->
      <section v-if="metrics?.admin">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">最近检测任务</span>
          </template>
          <DetectionTaskTimeline :tasks="[]" />
        </el-card>
      </section>

      <!-- 用户检测统计表 -->
      <section v-if="metrics?.admin">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">不同用户检测统计</span>
          </template>
          <div class="table-scroll">
            <el-table :data="metrics.admin.user_detection_stats" empty-text="暂无用户检测统计">
              <el-table-column prop="user_id" label="用户 ID" width="100" />
              <el-table-column prop="username" label="用户名" min-width="140" />
              <el-table-column prop="count" label="检测次数" width="120" align="center" />
            </el-table>
          </div>
        </el-card>
      </section>
    </AnimatedPage>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnimatedNumber from '@/components/common/AnimatedNumber.vue'
import MotionPanel from '@/components/common/MotionPanel.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'
import { getDashboardMetrics, type DashboardMetrics } from '@/api/dashboard'
import AnimatedPage from '@/components/common/AnimatedPage.vue'
import DetectionTaskTimeline from '@/components/detection/DetectionTaskTimeline.vue'

const metrics = ref<DashboardMetrics | null>(null)
const loading = ref(false)
const trendEl = ref<HTMLElement | null>(null)
const userTrendEl = ref<HTMLElement | null>(null)
const classEl = ref<HTMLElement | null>(null)
const modelEl = ref<HTMLElement | null>(null)
const aiEl = ref<HTMLElement | null>(null)
const resourceEl = ref<HTMLElement | null>(null)
const resourceSamples = ref<Array<{ time: string; cpu: number; memory: number; gpu: number }>>([])
let charts: echarts.ECharts[] = []
let timer: number | undefined

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

const chartPanels = computed(() => [
  { title: '近 7 日检测趋势', ref: true, assignRef: (el: HTMLElement) => { trendEl.value = el }, empty: false },
  { title: '用户检测趋势', ref: true, assignRef: (el: HTMLElement) => { userTrendEl.value = el }, empty: false },
  { title: '类别分布', ref: true, assignRef: (el: HTMLElement) => { classEl.value = el }, empty: false },
  { title: '模型调用排行', ref: true, assignRef: (el: HTMLElement) => { modelEl.value = el }, empty: false },
  { title: 'AI 调用趋势', ref: true, assignRef: (el: HTMLElement) => { aiEl.value = el }, empty: false },
  { title: '高频检测类别', ref: false, assignRef: () => {}, empty: !metrics.value?.top_detected_classes.length },
])

onMounted(async () => {
  await load()
  timer = window.setInterval(load, 15000)
})
onBeforeUnmount(() => {
  window.clearInterval(timer)
  charts.forEach((chart) => chart.dispose())
})

async function load() {
  loading.value = true
  try {
    metrics.value = await getDashboardMetrics()
    collectResourceSample()
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
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
function renderCharts() {
  charts.forEach((chart) => chart.dispose())
  charts = []
  if (!metrics.value) return
  renderTrendChart()
  renderUserTrendChart()
  renderClassChart()
  renderModelChart()
  renderAiChart()
  renderResourceChart()
}
function makeChart(el: HTMLElement | null) {
  if (!el) return null
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}
function renderTrendChart() {
  const chart = makeChart(trendEl.value)
  if (!chart || !metrics.value) return
  chart.setOption({
    color: ['#2563eb'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: metrics.value.daily_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.18 }, data: metrics.value.daily_trend_7d.map((item) => item.count) }],
  })
}
function renderUserTrendChart() {
  const chart = makeChart(userTrendEl.value)
  if (!chart || !metrics.value) return
  const users = Array.from(new Set(metrics.value.user_detection_trend_7d.flatMap((item) => Object.keys(item.users))))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 36, right: 16, top: 48, bottom: 28 },
    xAxis: { type: 'category', data: metrics.value.user_detection_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: users.map((name) => ({ name, type: 'line', smooth: true, data: metrics.value?.user_detection_trend_7d.map((item) => item.users[name] || 0) || [] })),
  })
}
function renderClassChart() {
  const chart = makeChart(classEl.value)
  if (!chart || !metrics.value) return
  chart.setOption({
    color: ['#ea580c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 48 },
    xAxis: { type: 'category', data: metrics.value.class_distribution.map((item) => item.class_zh || item.class), axisLabel: { rotate: 25 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', barWidth: 28, data: metrics.value.class_distribution.map((item) => item.count) }],
  })
}
function renderModelChart() {
  const chart = makeChart(modelEl.value)
  if (!chart || !metrics.value) return
  chart.setOption({
    color: ['#2563eb'],
    tooltip: { trigger: 'axis' },
    grid: { left: 92, right: 18, top: 24, bottom: 24 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: metrics.value.model_call_ranking.map((item) => item.model || '未命名') },
    series: [{ type: 'bar', data: metrics.value.model_call_ranking.map((item) => item.count) }],
  })
}
function renderAiChart() {
  const chart = makeChart(aiEl.value)
  if (!chart || !metrics.value) return
  chart.setOption({
    color: ['#0891b2'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: metrics.value.ai_call_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.16 }, data: metrics.value.ai_call_trend_7d.map((item) => item.count) }],
  })
}
function renderResourceChart() {
  const chart = makeChart(resourceEl.value)
  if (!chart) return
  chart.setOption({
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
function formatPercent(value?: number | null) {
  return value === null || value === undefined ? '不可用' : `${Number(value).toFixed(1)}%`
}
function formatBytes(value?: number | null) {
  if (!value) return '不可用'
  if (value >= 1024 ** 3) return `${(value / 1024 ** 3).toFixed(1)} GB`
  if (value >= 1024 ** 2) return `${(value / 1024 ** 2).toFixed(1)} MB`
  return `${value} B`
}
</script>

<style scoped>
/* Hero 横幅增强 */
.workstation-hero {
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 50%, #ecfeff 100%);
  border: 1px solid #bfdbfe;
  position: relative;
  overflow: hidden;
}

.workstation-hero::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.hero-info .hero-eyebrow {
  display: inline-block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  font-weight: 700;
  margin-bottom: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
}

.hero-stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-muted);
  font-weight: 600;
}

.hero-sep {
  color: var(--color-border);
  margin: 0 10px;
}

.hero-actions {
  flex-shrink: 0;
}

/* 指标卡片增强 */
.metric-card {
  position: relative;
  transition: transform var(--motion-fast) var(--ease-standard), box-shadow var(--motion-fast) var(--ease-standard);
}

.metric-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  opacity: 0;
  transition: opacity var(--motion-fast);
}

.metric-card:hover::before {
  opacity: 1;
}

/* 指标单位 */
.metric-unit {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-soft);
  margin-left: 3px;
}

/* 卡片标题行 */
.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-ink);
}

/* 健康列表 */
.health-list {
  display: grid;
  gap: 2px;
}

.diag-msg {
  font-size: 12px;
  color: var(--color-soft);
  text-align: right;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* GPU 设备列表 */
.gpu-device-list {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.gpu-device-card {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  transition: border-color var(--motion-fast);
}

.gpu-device-card:hover {
  border-color: var(--color-primary-light);
}

.gpu-device-card strong {
  display: block;
  font-size: 13px;
  color: var(--color-ink);
  margin-bottom: 6px;
}

.gpu-stats {
  display: flex;
  gap: 16px;
}

.gpu-stats span {
  font-size: 11px;
  color: var(--color-soft);
}

/* 迷你图表 */
.mini-chart {
  height: 240px;
  margin-top: 12px;
}

/* Top 类别列表 */
.top-class-list {
  display: grid;
  gap: 10px;
  padding: 4px 0;
}

.top-class-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--motion-fast);
}

.top-class-item:hover {
  background: var(--color-bg);
}

.class-name {
  font-size: 13px;
  color: var(--color-ink);
  font-weight: 600;
  min-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.class-bar-wrap {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: var(--color-border);
  overflow: hidden;
}

.class-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  transition: width var(--motion-slow) var(--ease-emphasized);
}

.class-count {
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 700;
  min-width: 36px;
  text-align: right;
}
</style>
