<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>检测任务运行概览</h1>
        <p>多维展示检测趋势、用户分布、模型调用、AI 调用与 GPU/CPU 资源状态。</p>
      </div>
      <el-button size="small" :loading="loading" @click="load">刷新数据</el-button>
    </div>

    <div class="ws-metrics-row">
      <div v-for="card in cards" :key="card.label" class="ws-metric">
        <span class="m-label">{{ card.label }}</span>
        <span class="m-value">{{ card.value }}</span>
        <span class="m-desc">{{ card.desc }}</span>
      </div>
    </div>

    <div v-if="metrics?.admin" class="ws-metrics-row">
      <div v-for="card in adminCards" :key="card.label" class="ws-metric">
        <span class="m-label">{{ card.label }}</span>
        <span class="m-value">{{ card.value }}</span>
        <span class="m-desc">{{ card.desc }}</span>
      </div>
    </div>

    <div v-if="metrics?.admin" class="ws-panel-2 mb-s">
      <div>
        <div class="ws-card">
          <div class="ws-card-header">系统资源快照</div>
          <div class="ws-card-body">
            <div class="ws-info-grid">
              <div class="ws-info-item"><span class="info-label">CPU 使用率</span><span class="info-value">{{ formatPercent(system?.cpu_percent) }}</span></div>
              <div class="ws-info-item"><span class="info-label">内存使用率</span><span class="info-value">{{ formatPercent(system?.memory?.percent) }}</span></div>
              <div class="ws-info-item"><span class="info-label">可用内存</span><span class="info-value">{{ formatBytes(system?.memory?.available) }}</span></div>
              <div class="ws-info-item"><span class="info-label">GPU 温度</span><span class="info-value">{{ system?.gpu_devices?.[0]?.temperature != null ? system.gpu_devices[0].temperature + '°C' : 'N/A' }}</span></div>
            </div>
          </div>
        </div>
        <div ref="resourceEl" class="ws-chart-box" style="margin-top:10px"></div>
      </div>
      <div class="ws-card">
        <div class="ws-card-header">GPU / CUDA 诊断</div>
        <div class="ws-card-body">
          <div class="ws-list">
            <div v-for="check in system?.diagnostics.checks || []" :key="check.name" class="ws-list-item">
              <el-tag :type="diagnosticTag(check.status)" size="small">{{ check.name }}</el-tag>
              <span class="li-name">{{ check.message }}</span>
            </div>
          </div>
          <div v-if="system?.gpu_devices.length" class="flex-gap" style="margin-top:8px">
            <div v-for="gpu in system.gpu_devices" :key="gpu.index" class="ws-info-item">
              <span class="info-label">{{ gpu.name }}</span>
              <span class="info-value" style="font-size:10px">显存：{{ formatBytes(gpu.allocated_memory) }} / {{ formatBytes(gpu.total_memory) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无可用 GPU 信息" />
        </div>
      </div>
    </div>

    <div class="ws-chart-grid mb-s">
      <div class="ws-chart-card"><div class="ws-card-header">近 7 日检测趋势</div><div class="ws-card-body"><div ref="trendEl" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">用户检测趋势</div><div class="ws-card-body"><div ref="userTrendEl" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">类别分布</div><div class="ws-card-body"><div ref="classEl" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">模型调用排行</div><div class="ws-card-body"><div ref="modelEl" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">AI 调用趋势</div><div class="ws-card-body"><div ref="aiEl" class="ws-chart-box" style="height:200px"></div></div></div>
      <div class="ws-chart-card"><div class="ws-card-header">高频检测类别</div><div class="ws-card-body">
        <div class="ws-list">
          <div v-for="item in metrics?.top_detected_classes || []" :key="item.class" class="ws-list-item">
            <span class="li-name">{{ item.class_zh || item.class }}</span>
            <span class="li-extra">{{ item.count }}</span>
          </div>
        </div>
        <el-empty v-if="!metrics?.top_detected_classes.length" description="暂无类别统计" />
      </div></div>
    </div>

    <div v-if="metrics?.admin" class="ws-card">
      <div class="ws-card-header">不同用户检测统计</div>
      <div class="ws-card-body">
        <el-table :data="metrics.admin.user_detection_stats" empty-text="暂无用户检测统计">
          <el-table-column prop="user_id" label="用户ID" width="100" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="count" label="检测次数" width="130" />
        </el-table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getDashboardMetrics, type DashboardMetrics } from '@/api/dashboard'

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

onMounted(async () => { await load(); timer = window.setInterval(load, 15000) })
onBeforeUnmount(() => { window.clearInterval(timer); charts.forEach((chart) => chart.dispose()) })

async function load() {
  loading.value = true
  try {
    metrics.value = await getDashboardMetrics(); collectResourceSample(); await nextTick(); renderCharts()
  } finally { loading.value = false }
}
function collectResourceSample() {
  if (!system.value) return
  const gpu = system.value.gpu_devices[0]
  resourceSamples.value.push({ time: new Date().toLocaleTimeString('zh-CN', { hour12: false }), cpu: Number(system.value.cpu_percent || 0), memory: Number(system.value.memory?.percent || 0), gpu: gpu ? Math.round((gpu.reserved_memory / Math.max(1, gpu.total_memory)) * 100) : 0 })
  resourceSamples.value = resourceSamples.value.slice(-12)
}
function renderCharts() { charts.forEach((chart) => chart.dispose()); charts = []; if (!metrics.value) return; renderTrendChart(); renderUserTrendChart(); renderClassChart(); renderModelChart(); renderAiChart(); renderResourceChart() }
function makeChart(el: HTMLElement | null) { if (!el) return null; const chart = echarts.init(el, null, { backgroundColor: 'transparent' } as any); charts.push(chart); return chart }

function renderTrendChart() { const chart = makeChart(trendEl.value); if (!chart || !metrics.value) return; chart.setOption({ color: ['#58a6ff'], tooltip: { trigger: 'axis' }, grid: { left: 40, right: 16, top: 12, bottom: 24 }, xAxis: { type: 'category', data: metrics.value.daily_trend_7d.map((item) => item.date.slice(5)), axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.14 }, data: metrics.value.daily_trend_7d.map((item) => item.count) }] }) }
function renderUserTrendChart() { const chart = makeChart(userTrendEl.value); if (!chart || !metrics.value) return; const users = Array.from(new Set(metrics.value.user_detection_trend_7d.flatMap((item) => Object.keys(item.users)))); chart.setOption({ tooltip: { trigger: 'axis' }, legend: { top: 0, type: 'scroll', textStyle: { color: '#8b949e', fontSize: 10 } }, grid: { left: 40, right: 16, top: 28, bottom: 24 }, xAxis: { type: 'category', data: metrics.value.user_detection_trend_7d.map((item) => item.date.slice(5)), axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: users.map((name) => ({ name, type: 'line', smooth: true, data: metrics.value?.user_detection_trend_7d.map((item) => item.users[name] || 0) || [] })) }) }
function renderClassChart() { const chart = makeChart(classEl.value); if (!chart || !metrics.value) return; chart.setOption({ color: ['#3fb950'], tooltip: { trigger: 'axis' }, grid: { left: 40, right: 16, top: 12, bottom: 40 }, xAxis: { type: 'category', data: metrics.value.class_distribution.map((item) => item.class_zh || item.class), axisLabel: { rotate: 25, color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [{ type: 'bar', barWidth: 24, data: metrics.value.class_distribution.map((item) => item.count) }] }) }
function renderModelChart() { const chart = makeChart(modelEl.value); if (!chart || !metrics.value) return; chart.setOption({ color: ['#58a6ff'], tooltip: { trigger: 'axis' }, grid: { left: 100, right: 18, top: 8, bottom: 8 }, xAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, yAxis: { type: 'category', data: metrics.value.model_call_ranking.map((item) => item.model || '未命名'), axisLabel: { color: '#8b949e' } }, series: [{ type: 'bar', data: metrics.value.model_call_ranking.map((item) => item.count) }] }) }
function renderAiChart() { const chart = makeChart(aiEl.value); if (!chart || !metrics.value) return; chart.setOption({ color: ['#d29922'], tooltip: { trigger: 'axis' }, grid: { left: 40, right: 16, top: 12, bottom: 24 }, xAxis: { type: 'category', data: metrics.value.ai_call_trend_7d.map((item) => item.date.slice(5)), axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.14 }, data: metrics.value.ai_call_trend_7d.map((item) => item.count) }] }) }
function renderResourceChart() { const chart = makeChart(resourceEl.value); if (!chart) return; chart.setOption({ tooltip: { trigger: 'axis' }, legend: { top: 0, textStyle: { color: '#8b949e', fontSize: 10 } }, grid: { left: 40, right: 14, top: 18, bottom: 24 }, xAxis: { type: 'category', data: resourceSamples.value.map((item) => item.time), axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } }, yAxis: { type: 'value', max: 100, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } }, series: [{ name: 'CPU', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.cpu) }, { name: '内存', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.memory) }, { name: 'GPU显存', type: 'line', smooth: true, data: resourceSamples.value.map((item) => item.gpu) }] }) }

function diagnosticTag(status: string) { if (status === 'ok') return 'success'; if (status === 'warning') return 'warning'; if (status === 'error') return 'danger'; return 'info' }
function formatPercent(value?: number | null) { return value === null || value === undefined ? 'N/A' : `${Number(value).toFixed(1)}%` }
function formatBytes(value?: number | null) { if (!value) return 'N/A'; if (value >= 1024 ** 3) return `${(value / 1024 ** 3).toFixed(1)} GB`; if (value >= 1024 ** 2) return `${(value / 1024 ** 2).toFixed(1)} MB`; return `${value} B` }
</script>
