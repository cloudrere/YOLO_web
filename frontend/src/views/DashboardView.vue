<template>
  <AppLayout>
    <section class="dashboard-banner glass-card">
      <div>
        <span class="eyebrow dark">实时统计</span>
        <h2>检测任务运行概览</h2>
        <p>所有指标均来自检测历史、系统状态与结构化检测结果，方便快速判断平台使用情况。</p>
      </div>
      <el-button type="primary" @click="load">刷新数据</el-button>
    </section>
    <section class="grid metrics">
      <el-card v-for="card in cards" :key="card.label" shadow="never" class="metric-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.desc }}</small>
      </el-card>
    </section>

    <section v-if="metrics?.admin" class="grid four admin-metrics">
      <el-card v-for="card in adminCards" :key="card.label" shadow="never" class="metric-card compact-metric">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.desc }}</small>
      </el-card>
    </section>

    <section v-if="metrics?.admin" class="grid two system-grid">
      <el-card shadow="never" class="panel-card status-panel">
        <template #header>系统状态</template>
        <div class="system-status-list">
          <div><span>CPU 使用率</span><strong>{{ formatPercent(metrics.admin.system_status.cpu_percent) }}</strong></div>
          <div><span>内存使用率</span><strong>{{ formatPercent(metrics.admin.system_status.memory?.percent) }}</strong></div>
          <div><span>可用内存</span><strong>{{ formatBytes(metrics.admin.system_status.memory?.available) }}</strong></div>
          <div><span>温度</span><strong>{{ metrics.admin.system_status.temperature ?? '不可用' }}</strong></div>
        </div>
      </el-card>
      <el-card shadow="never" class="panel-card status-panel">
        <template #header>GPU 状态</template>
        <div v-if="metrics.admin.system_status.gpu_devices.length" class="gpu-list">
          <div v-for="gpu in metrics.admin.system_status.gpu_devices" :key="gpu.index" class="gpu-card">
            <strong>{{ gpu.name }}</strong>
            <span>显存：{{ formatBytes(gpu.allocated_memory) }} / {{ formatBytes(gpu.total_memory) }}</span>
            <span>温度：{{ gpu.temperature ?? '不可用' }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无可用 GPU 信息" />
      </el-card>
    </section>

    <section class="grid two chart-grid">
      <el-card shadow="never" class="panel-card chart-panel">
        <template #header>近 7 日检测趋势</template>
        <div ref="trendEl" class="chart"></div>
      </el-card>
      <el-card shadow="never" class="panel-card chart-panel">
        <template #header>高频检测类别</template>
        <div ref="classEl" class="chart"></div>
      </el-card>
    </section>

    <el-card v-if="metrics?.admin" shadow="never" class="panel-card">
      <template #header>不同用户检测统计</template>
      <div class="table-scroll">
        <el-table :data="metrics.admin.user_detection_stats">
          <el-table-column prop="user_id" label="用户ID" width="100" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="count" label="检测次数" width="130" />
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getDashboardMetrics, type DashboardMetrics } from '@/api/dashboard'

const metrics = ref<DashboardMetrics | null>(null)
const trendEl = ref<HTMLElement | null>(null)
const classEl = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let classChart: echarts.ECharts | null = null

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

onMounted(load)

async function load() {
  metrics.value = await getDashboardMetrics()
  await nextTick()
  renderCharts()
}
function renderCharts() {
  if (!metrics.value || !trendEl.value || !classEl.value) return
  trendChart?.dispose()
  classChart?.dispose()
  trendChart = echarts.init(trendEl.value)
  classChart = echarts.init(classEl.value)
  trendChart.setOption({
    color: ['#1f6f5b'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: metrics.value.daily_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.18 }, data: metrics.value.daily_trend_7d.map((item) => item.count) }],
  })
  classChart.setOption({
    color: ['#d39a2d'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 40 },
    xAxis: { type: 'category', data: metrics.value.top_detected_classes.map((item) => item.class_zh || item.class) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', barWidth: 28, data: metrics.value.top_detected_classes.map((item) => item.count) }],
  })
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
