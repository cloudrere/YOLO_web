<template>
  <AppLayout>
    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="toolbar">
          <span>检测历史</span>
          <el-button @click="load">刷新</el-button>
        </div>
      </template>
      <el-form :inline="true" :model="filters" class="filter-bar">
        <el-form-item label="来源类型">
          <el-select v-model="filters.source_type" clearable placeholder="全部" style="width: 180px">
            <el-option label="单图" value="image" />
            <el-option label="批量图片" value="batch_image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-input v-model="filters.class_name" clearable placeholder="输入类别名" />
        </el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>
      <div class="table-scroll">
        <el-table :data="rows" @row-click="openDetail">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="source_type" label="来源" width="130" />
          <el-table-column prop="file_name" label="文件名" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="result_count" label="目标数" width="100" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="130" />
          <el-table-column prop="created_at" label="创建时间" width="190" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click.stop="remove(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
    </el-card>
    <el-drawer v-model="drawer" title="检测详情" size="52%">
      <div v-if="detail?.result_url" class="media-preview annotated-preview history-preview">
        <img :src="mediaUrl(detail.result_url)" :alt="detail.file_name" />
      </div>
      <DetectionResultTable :results="detail?.results || []" />
      <AnalysisPanel v-if="detail?.analysis" :analysis="detail.analysis" />
      <pre v-if="detail" class="json-box">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { apiMediaUrl } from '@/api/detect'
import { deleteHistory, getHistory, listHistory, type HistoryDetail, type HistoryItem } from '@/api/history'

const rows = ref<HistoryItem[]>([])
const detail = ref<HistoryDetail | null>(null)
const drawer = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filters = reactive({ source_type: '', class_name: '' })

function mediaUrl(path: string) {
  return apiMediaUrl(path)
}
async function load() {
  const data = await listHistory({ page: page.value, page_size: pageSize, ...filters })
  rows.value = data.items
  total.value = data.total
}
async function openDetail(row: HistoryItem) {
  detail.value = await getHistory(row.id)
  drawer.value = true
}
async function remove(id: number) {
  await deleteHistory(id)
  await load()
}
onMounted(load)
</script>
