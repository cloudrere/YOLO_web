<template>
  <AppLayout>
    <section class="grid metrics">
      <el-card v-for="card in cards" :key="card.label" shadow="never" class="metric-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </el-card>
    </section>
    <section class="grid two">
      <el-card shadow="never">
        <template #header>Daily Trend (7 days)</template>
        <div ref="trendEl" class="chart"></div>
      </el-card>
      <el-card shadow="never">
        <template #header>Top Detected Classes</template>
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
  { label: 'Total Detections', value: metrics.value?.total_detections ?? 0 },
  { label: 'Image Records', value: metrics.value?.image_count ?? 0 },
  { label: 'Video Records', value: metrics.value?.video_count ?? 0 },
  { label: 'Active Users', value: metrics.value?.active_users ?? 0 },
])

onMounted(async () => {
  metrics.value = await getDashboardMetrics()
  renderCharts()
})

function renderCharts() {
  if (!metrics.value || !trendEl.value || !classEl.value) return
  echarts.init(trendEl.value).setOption({
    tooltip: {},
    xAxis: { type: 'category', data: metrics.value.daily_trend_7d.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: {}, data: metrics.value.daily_trend_7d.map((item) => item.count) }],
  })
  echarts.init(classEl.value).setOption({
    tooltip: {},
    xAxis: { type: 'category', data: metrics.value.top_detected_classes.map((item) => item.class) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: metrics.value.top_detected_classes.map((item) => item.count) }],
  })
}
</script>
