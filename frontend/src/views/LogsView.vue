<template>
  <AppLayout>
    <section class="logs-hero panel-card">
      <div class="logs-hero-info">
        <span class="logs-eyebrow">System Logs</span>
        <h2>系统日志</h2>
        <p>查看和管理系统运行日志，支持按级别、模块和时间范围筛选。</p>
      </div>
      <div class="logs-hero-stats">
        <div class="logs-stat">
          <strong>{{ total }}</strong>
          <span>日志总数</span>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </section>

    <el-card shadow="never" class="panel-card logs-main-card">
      <div class="logs-filter-bar">
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
          <el-form-item label="日期范围">
            <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD HH:mm:ss" start-placeholder="开始日期" end-placeholder="结束日期" />
          </el-form-item>
        </el-form>
        <div class="logs-action-bar">
          <el-button type="primary" @click="load">查询</el-button>
          <el-button type="warning" :disabled="!dateRange?.length" @click="removeByDate">按日期删除</el-button>
          <el-button type="danger" :disabled="!selectedRows.length" @click="removeSelected">批量删除 ({{ selectedRows.length }})</el-button>
        </div>
      </div>
      <div class="table-scroll log-table-shell">
        <TransitionGroup name="list" tag="div">
          <el-table :key="page" :data="rows" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="48" />
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="级别" width="130">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.level)" effect="dark">
                  <StatusPulse :status="levelToStatus(row.level)" size="sm" />
                  {{ row.level_zh || row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="模块" width="150">
              <template #default="{ row }">{{ row.module_zh || row.module }}<small class="sub-text">{{ row.module }}</small></template>
            </el-table-column>
            <el-table-column label="类型" width="160">
              <template #default="{ row }">{{ row.type_zh || row.type }}<small class="sub-text">{{ row.type }}</small></template>
            </el-table-column>
            <el-table-column prop="message" label="消息" min-width="260" />
            <el-table-column prop="created_at" label="创建时间" width="190" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }"><el-button type="danger" size="small" @click="remove(row.id)">删除</el-button></template>
            </el-table-column>
          </el-table>
        </TransitionGroup>
      </div>
      <div class="pagination-footer">
        <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" background @current-change="load" />
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'
import { deleteLog, deleteLogsBatch, deleteLogsByDate, listLogs, type LogItem } from '@/api/log'

const rows = ref<LogItem[]>([])
const selectedRows = ref<LogItem[]>([])
const dateRange = ref<[string, string] | null>(null)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const filters = reactive({ level: '', module: '', log_type: '' })
async function load() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries({ page: page.value, page_size: pageSize, ...filters }).filter(([, value]) => value !== ''))
    const data = await listLogs(params)
    rows.value = data.items
    total.value = data.total
    selectedRows.value = []
  } finally {
    loading.value = false
  }
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
function levelToStatus(level: string) {
  if (['error', 'critical'].includes(level)) return 'danger'
  if (level === 'warning') return 'warning'
  if (level === 'info') return 'success'
  return 'idle'
}
onMounted(load)
</script>

<style scoped>
.logs-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: var(--gap);
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid var(--color-border);
}

.logs-eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-muted);
  margin-bottom: 4px;
}

.logs-hero-info h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 800;
  color: var(--color-ink);
}

.logs-hero-info p {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
}

.logs-hero-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.logs-stat {
  text-align: center;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.logs-stat strong {
  display: block;
  font-size: 20px;
  font-weight: 800;
  color: var(--color-primary);
}

.logs-stat span {
  display: block;
  font-size: 11px;
  color: var(--color-soft);
}

.logs-filter-bar {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.logs-action-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.logs-main-card :deep(.el-card__body) {
  padding-top: 20px;
}

.el-table :deep(.el-tag) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 768px) {
  .logs-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>