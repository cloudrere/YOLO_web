<template>
  <AppLayout>
    <el-card shadow="never">
      <template #header>
        <div class="toolbar">
          <span>Detection History</span>
          <el-button @click="load">Refresh</el-button>
        </div>
      </template>
      <el-form :inline="true" :model="filters">
        <el-form-item label="Source">
          <el-select v-model="filters.source_type" clearable placeholder="All" style="width: 160px">
            <el-option label="Image" value="image" />
            <el-option label="Batch Image" value="batch_image" />
            <el-option label="Video" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="Class">
          <el-input v-model="filters.class_name" clearable placeholder="Class name" />
        </el-form-item>
        <el-button type="primary" @click="load">Search</el-button>
      </el-form>
      <el-table :data="rows" @row-click="openDetail">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="source_type" label="Source" width="130" />
        <el-table-column prop="file_name" label="File" />
        <el-table-column prop="status" label="Status" width="100" />
        <el-table-column prop="result_count" label="Results" width="100" />
        <el-table-column prop="duration_ms" label="Duration(ms)" width="130" />
        <el-table-column prop="created_at" label="Created" width="190" />
        <el-table-column label="Actions" width="120">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click.stop="remove(row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
    </el-card>
    <el-drawer v-model="drawer" title="Detection Detail" size="50%">
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
import { deleteHistory, getHistory, listHistory, type HistoryDetail, type HistoryItem } from '@/api/history'

const rows = ref<HistoryItem[]>([])
const detail = ref<HistoryDetail | null>(null)
const drawer = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filters = reactive({ source_type: '', class_name: '' })

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
