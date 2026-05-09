<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>日志中心</h2>
        <p>系统登录、检测、模型切换与任务执行日志</p>
      </div>
      <el-button size="small" @click="load">刷新</el-button>
    </div>

    <el-card shadow="never">
      <div class="filter-bar">
        <el-select v-model="filters.level" clearable placeholder="级别" style="width:110px">
          <el-option label="信息" value="信息" />
          <el-option label="警告" value="警告" />
          <el-option label="错误" value="错误" />
          <el-option label="严重" value="严重" />
        </el-select>
        <el-input v-model="filters.module" clearable placeholder="模块" style="width:130px" />
        <el-input v-model="filters.log_type" clearable placeholder="日志类型" style="width:130px" />
        <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD HH:mm:ss" start-placeholder="开始日期" end-placeholder="结束日期" style="width:240px" />
        <el-button type="primary" size="small" @click="load">查询</el-button>
        <el-button type="danger" size="small" :disabled="!selectedRows.length" @click="removeSelected">批量删除</el-button>
        <el-button type="warning" size="small" :disabled="!dateRange?.length" @click="removeByDate">按日期删除</el-button>
      </div>

      <div class="table-wrap">
        <el-table :data="rows" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="48" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="级别" width="110">
            <template #default="{ row }"><el-tag :type="levelTag(row.level)" size="small">{{ row.level_zh || row.level }}</el-tag></template>
          </el-table-column>
          <el-table-column label="模块" width="140">
            <template #default="{ row }">{{ row.module_zh || row.module }}<span style="font-size:11px;color:#909399;margin-left:4px">{{ row.module }}</span></template>
          </el-table-column>
          <el-table-column label="类型" width="150">
            <template #default="{ row }">{{ row.type_zh || row.type }}<span style="font-size:11px;color:#909399;margin-left:4px">{{ row.type }}</span></template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="260" />
          <el-table-column prop="created_at" label="创建时间" width="190" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }"><el-button type="danger" size="small" @click="remove(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
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
  const data = await listLogs(params); rows.value = data.items; total.value = data.total; selectedRows.value = []
}
function handleSelectionChange(selection: LogItem[]) { selectedRows.value = selection }
async function remove(id: number) {
  try { await ElMessageBox.confirm('确认删除这条日志吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }
  const data = await deleteLog(id); ElMessage.success(`已删除 ${data.deleted} 条日志`); await load()
}
async function removeSelected() {
  if (!selectedRows.value.length) return
  try { await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条日志吗？`, '批量删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }
  const data = await deleteLogsBatch(selectedRows.value.map((row) => row.id)); ElMessage.success(`已删除 ${data.deleted} 条日志`); await load()
}
async function removeByDate() {
  if (!dateRange.value?.length) return
  try { await ElMessageBox.confirm(`确认删除 ${dateRange.value[0]} 至 ${dateRange.value[1]} 的日志吗？`, '按日期删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }
  const data = await deleteLogsByDate(dateRange.value[0], dateRange.value[1]); ElMessage.success(`已删除 ${data.deleted} 条日志`); dateRange.value = null; await load()
}
function levelTag(level: string) { if (['error', 'critical'].includes(level)) return 'danger'; if (level === 'warning') return 'warning'; return 'info' }
onMounted(load)
</script>
