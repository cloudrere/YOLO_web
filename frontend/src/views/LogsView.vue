<template>
  <AppLayout>
    <el-card shadow="never">
      <template #header>
        <div class="toolbar"><span>System Logs</span><el-button @click="load">Refresh</el-button></div>
      </template>
      <el-form :inline="true" :model="filters">
        <el-form-item label="Level"><el-input v-model="filters.level" clearable /></el-form-item>
        <el-form-item label="Module"><el-input v-model="filters.module" clearable /></el-form-item>
        <el-form-item label="Type"><el-input v-model="filters.log_type" clearable /></el-form-item>
        <el-button type="primary" @click="load">Search</el-button>
      </el-form>
      <el-table :data="rows">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="level" label="Level" width="100" />
        <el-table-column prop="module" label="Module" width="120" />
        <el-table-column prop="type" label="Type" width="120" />
        <el-table-column prop="message" label="Message" />
        <el-table-column prop="created_at" label="Created" width="190" />
      </el-table>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { listLogs, type LogItem } from '@/api/log'

const rows = ref<LogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filters = reactive({ level: '', module: '', log_type: '' })
async function load() {
  const data = await listLogs({ page: page.value, page_size: pageSize, ...filters })
  rows.value = data.items
  total.value = data.total
}
onMounted(load)
</script>
