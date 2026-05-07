<template>
  <AppLayout>
    <section class="dashboard-banner glass-card">
      <div>
        <span class="eyebrow dark">实时统计</span>
        <h2>检测任务运行概览</h2>
        <p>所有指标均来自检测历史与结构化检测结果，方便快速判断平台使用情况。</p>
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
    <section class="grid two">
      <el-card shadow="never" class="panel-card">
        <template #header>近 7 日检测趋势</template>
        <div ref="trendEl" class="chart"></div>
      </el-card>
      <el-card shadow="never" class="panel-card">
        <template #header>高频检测类别</template>
        <div ref="classEl" class="chart"></div>
      </el-card>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AppLayout from '@/components/layout/AppLayout.vue'
import { getDashboardMetrics, type DashboardMetrics } from '@/api/dashboard'

const metrics = ref<DashboardMetrics | null>(null)
const trendEl = ref<HTMLElement | null>(null)
const classEl = ref<HTMLElement | null>(null)
const cards = computed(() => [
  { label: '检测记录总数', value: metrics.value?.total_detections ?? 0, desc: 'DetectionRecord 总量' },
  { label: '图片检测', value: metrics.value?.image_count ?? 0, desc: '单图与批量图片' },
  { label: '视频检测', value: metrics.value?.video_count ?? 0, desc: '异步视频任务' },
  { label: '活跃用户', value: metrics.value?.active_users ?? 0, desc: '可登录账号数' },
])

onMounted(load)

async function load() {
  metrics.value = await getDashboardMetrics()
  renderCharts()
}

function renderCharts() {
  if (!metrics.value || !trendEl.value || !classEl.value) return
  echarts.init(trendEl.value).setOption({
    color: ['#1f6f5b'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 28 },
    xAxis: { type: 'category', data: metrics.value.daily_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.18 }, data: metrics.value.daily_trend_7d.map((item) => item.count) }],
  })
  echarts.init(classEl.value).setOption({
    color: ['#d39a2d'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 28, bottom: 40 },
    xAxis: { type: 'category', data: metrics.value.top_detected_classes.map((item) => item.class) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', barWidth: 28, data: metrics.value.top_detected_classes.map((item) => item.count) }],
  })
}
</script>
