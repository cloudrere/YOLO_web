<template>
  <AppLayout>
    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="toolbar"><span>系统日志</span><el-button @click="load">刷新</el-button></div>
      </template>
      <el-form :inline="true" :model="filters" class="filter-bar">
        <el-form-item label="级别">
          <el-select v-model="filters.level" clearable placeholder="全部" style="width: 150px">
            <el-option label="信息" value="信息" />
            <el-option label="警告" value="警告" />
            <el-option label="错误" value="错误" />
            <el-option label="严重" value="严重" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块"><el-input v-model="filters.module" clearable placeholder="检测 / 模型 / AI助手" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="filters.log_type" clearable placeholder="日志类型" /></el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>
      <div class="table-scroll log-table-shell">
        <el-table :data="rows">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="级别" width="130">
            <template #default="{ row }"><el-tag :type="levelTag(row.level)">{{ row.level_zh || row.level }}</el-tag></template>
          </el-table-column>
          <el-table-column label="模块" width="150">
            <template #default="{ row }">{{ row.module_zh || row.module }}<small class="sub-text">{{ row.module }}</small></template>
          </el-table-column>
          <el-table-column label="类型" width="160">
            <template #default="{ row }">{{ row.type_zh || row.type }}<small class="sub-text">{{ row.type }}</small></template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="260" />
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
  const params = Object.fromEntries(Object.entries({ page: page.value, page_size: pageSize, ...filters }).filter(([, value]) => value !== ''))
  const data = await listLogs(params)
  rows.value = data.items
  total.value = data.total
}
function levelTag(level: string) {
  if (['error', 'critical'].includes(level)) return 'danger'
  if (level === 'warning') return 'warning'
  return 'info'
}
onMounted(load)
</script>
