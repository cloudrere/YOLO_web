<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>系统日志</h2>
        <p>按级别、模块、类型或时间范围检索系统运行日志，用于排查推理异常、设备故障和系统错误。</p>
      </div>
      <div class="flex-wrap">
        <el-button type="danger" size="small" :disabled="!selectedRows.length" @click="removeSelected">批量删除</el-button>
        <el-button type="warning" size="small" :disabled="!dateRange?.length" @click="removeByDate">按日期删除</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </section>

    <el-card shadow="never">
      <el-form :inline="true" :model="filters" class="filter-bar" style="margin-bottom:12px;">
        <el-form-item label="级别">
          <el-select v-model="filters.level" clearable placeholder="全部" style="width:130px;">
            <el-option label="信息" value="信息" />
            <el-option label="警告" value="警告" />
            <el-option label="错误" value="错误" />
            <el-option label="严重" value="严重" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块"><el-input v-model="filters.module" clearable placeholder="检测 / 模型 / AI助手" style="width:150px;" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="filters.log_type" clearable placeholder="日志类型" style="width:130px;" /></el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD HH:mm:ss" start-placeholder="开始" end-placeholder="结束" style="width:240px;" />
        </el-form-item>
        <el-form-item><el-button type="primary" @click="load">查询</el-button></el-form-item>
      </el-form>

      <div class="table-scroll">
        <el-table :data="rows" @selection-change="handleSelectionChange" size="small">
          <el-table-column type="selection" width="44" />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="级别" width="100">
            <template #default="{ row }"><el-tag :type="levelTag(row.level)" size="small">{{ row.level_zh || row.level }}</el-tag></template>
          </el-table-column>
          <el-table-column label="模块" width="140">
            <template #default="{ row }">{{ row.module_zh || row.module }}<small style="display:block;color:var(--color-muted);">{{ row.module }}</small></template>
          </el-table-column>
          <el-table-column label="类型" width="150">
            <template #default="{ row }">{{ row.type_zh || row.type }}<small style="display:block;color:var(--color-muted);">{{ row.type }}</small></template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="260" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }"><el-button type="danger" size="small" @click="remove(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
      </div>

      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" style="margin-top:12px;" />
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { deleteLog, deleteLogsBatch, deleteLogsByDate, listLogs, type LogItem } from '@/api/log'

const rows = ref<LogItem[]>([])
const selectedRows = ref<LogItem[]>([])
const dateRange = ref<[string, string] | null>(null)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filters = reactive({ level: '', module: '', log_type: '' })
async function load() {
  const params = Object.fromEntries(Object.entries({ page: page.value, page_size: pageSize, ...filters }).filter(([, value]) => value !== ''))
  const data = await listLogs(params)
  rows.value = data.items
  total.value = data.total
  selectedRows.value = []
}
function handleSelectionChange(selection: LogItem[]) {
  selectedRows.value = selection
}
async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这条日志吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  const data = await deleteLog(id)
  ElMessage.success(`已删除 ${data.deleted} 条日志`)
  await load()
}
async function removeSelected() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条日志吗？删除后不可恢复。`, '批量删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  const data = await deleteLogsBatch(selectedRows.value.map((row) => row.id))
  ElMessage.success(`已删除 ${data.deleted} 条日志`)
  await load()
}
async function removeByDate() {
  if (!dateRange.value?.length) return
  try {
    await ElMessageBox.confirm(`确认删除 ${dateRange.value[0]} 至 ${dateRange.value[1]} 的日志吗？删除后不可恢复。`, '按日期删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  const data = await deleteLogsByDate(dateRange.value[0], dateRange.value[1])
  ElMessage.success(`已删除 ${data.deleted} 条日志`)
  dateRange.value = null
  await load()
}
function levelTag(level: string) {
  if (['error', 'critical'].includes(level)) return 'danger'
  if (level === 'warning') return 'warning'
  return 'info'
}
onMounted(load)
</script>
