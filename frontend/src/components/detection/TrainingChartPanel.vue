<template>
  <el-card shadow="never">
    <template #header><span style="font-weight:700;">{{ title }}</span></template>
    <div :ref="(el: any) => setRef(el)" class="chart"></div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  title: string
  option: Record<string, unknown>
  watchKey?: number
}>()

let chart: echarts.ECharts | null = null
const container = ref<HTMLElement | null>(null)

function setRef(el: HTMLElement | null) { container.value = el }

function render() {
  if (!container.value) return
  if (!chart) { chart = echarts.init(container.value) }
  chart.setOption(props.option as echarts.EChartsOption, true)
}

onMounted(render)
onBeforeUnmount(() => { chart?.dispose(); chart = null })
watch(() => props.watchKey, render)
watch(() => props.option, render, { deep: true })
</script>
