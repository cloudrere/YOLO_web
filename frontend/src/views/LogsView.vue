<template>
  <AppLayout>
    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="toolbar"><span>系统日志</span><el-button @click="load">刷新</el-button></div>
      </template>
      <el-form :inline="true" :model="filters" class="filter-bar">
        <el-form-item label="级别"><el-input v-model="filters.level" clearable placeholder="日志级别" /></el-form-item>
        <el-form-item label="模块"><el-input v-model="filters.module" clearable placeholder="业务模块" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="filters.log_type" clearable placeholder="日志类型" /></el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>
      <div class="table-scroll log-table-shell">
        <el-table :data="rows">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="level" label="级别" width="100" />
          <el-table-column prop="module" label="模块" width="120" />
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column prop="message" label="消息" />
          <el-table-column prop="created_at" label="创建时间" width="190" />
        </el-table>
      </div>
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
