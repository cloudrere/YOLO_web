<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>检测结果中心</h2>
        <p>按来源、类别、用户追溯检测记录，查看完整检测证据链 — 原图/检测图/视频/结果与 AI 分析。</p>
      </div>
      <div class="flex-wrap">
        <el-button type="danger" size="small" :disabled="!selectedRows.length" @click="removeSelected">批量删除</el-button>
        <el-button size="small" @click="exportRows">导出 Excel</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </section>

    <el-card shadow="never" style="margin-bottom:var(--gap);">
      <!-- 筛选栏 -->
      <el-form :inline="true" :model="filters" class="filter-bar">
        <el-form-item label="来源"><el-select v-model="filters.source_type" clearable placeholder="全部" style="width:140px;"><el-option label="单图" value="image" /><el-option label="批量" value="batch_image" /><el-option label="视频" value="video" /></el-select></el-form-item>
        <el-form-item label="英文类别"><el-input v-model="filters.class_name" clearable placeholder="person/car" style="width:140px;" /></el-form-item>
        <el-form-item label="中文类别"><el-input v-model="filters.class_name_zh" clearable placeholder="人/汽车" style="width:140px;" /></el-form-item>
        <el-form-item label="用户"><el-input v-model="filters.username" clearable placeholder="用户名" style="width:120px;" /></el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>

      <!-- 结果列表 -->
      <div class="table-scroll">
        <el-table :data="rows" @row-click="openDetail" @selection-change="handleSelectionChange" size="small">
          <el-table-column type="selection" width="44" />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="预览" width="170">
            <template #default="{ row }">
              <div class="thumb-pair" :class="{ 'video-thumb-pair': row.source_type === 'video' }">
                <template v-if="row.source_type === 'video'">
                  <div style="position:relative;overflow:hidden;border-radius:6px;min-height:64px;background:#0f172a;">
                    <img v-if="videoThumbUrl(row)" :src="mediaUrl(videoThumbUrl(row))" alt="视频缩略" style="width:100%;height:64px;object-fit:cover;" />
                    <button type="button" @click.stop="openDetail(row)" style="position:absolute;right:6px;bottom:6px;border:0;border-radius:99px;padding:3px 8px;background:#ea580c;color:#fff;font-size:11px;font-weight:700;cursor:pointer;">播放</button>
                  </div>
                </template>
                <template v-else>
                  <img v-if="row.original_url" :src="mediaUrl(row.original_url)" alt="原图" />
                  <img v-if="row.result_url" :src="mediaUrl(row.result_url)" alt="检测图" />
                </template>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="100" />
          <el-table-column prop="username" label="用户" width="100" />
          <el-table-column prop="file_name" label="文件名" min-width="160" show-overflow-tooltip />
          <el-table-column label="类别" min-width="180">
            <template #default="{ row }">
              <el-tag v-for="item in row.classes" :key="`${item.class}-${item.class_zh}`" class="tag" type="success" size="small">{{ item.class_zh || item.class }} {{ item.count }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column prop="result_count" label="目标数" width="90" />
          <el-table-column prop="duration_ms" label="耗时ms" width="100" />
          <el-table-column prop="created_at_text" label="检测时间" width="170" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }"><el-button type="danger" size="small" @click.stop="remove(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
    </el-card>

    <!-- 检测证据详情抽屉 -->
    <el-drawer v-model="drawer" title="检测证据详情" size="68%">
      <div v-if="detail">
        <!-- 元数据 -->
        <div class="evidence-meta-grid" style="margin-bottom:var(--gap);">
          <div class="evidence-meta-item"><span>用户</span><strong>{{ detail.username || detail.user_id || '暂无' }}</strong></div>
          <div class="evidence-meta-item"><span>模型</span><strong>{{ detail.model_name || '暂无' }}</strong></div>
          <div class="evidence-meta-item"><span>设备</span><strong>{{ detail.device || '暂无' }}</strong></div>
          <div class="evidence-meta-item"><span>检测时间</span><strong>{{ detail.created_at_text || detail.created_at }}</strong></div>
          <div class="evidence-meta-item"><span>来源</span><strong>{{ detail.source_type }}</strong></div>
          <div class="evidence-meta-item"><span>参数</span><strong>{{ formatParameters(detail) }}</strong></div>
        </div>

        <!-- 证据面板：图片/视频/结果/AI分析 -->
        <ResultEvidencePanel :detail="detail" />

        <!-- 原始 JSON -->
        <details style="margin-top:var(--gap);">
          <summary style="cursor:pointer;font-size:12px;color:var(--color-muted);font-weight:600;">完整 JSON 数据</summary>
          <pre class="json-box">{{ JSON.stringify(detail, null, 2) }}</pre>
        </details>
      </div>
      <el-empty v-else description="请点击一条检测记录查看详情" />
    </el-drawer>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import ResultEvidencePanel from '@/components/detection/ResultEvidencePanel.vue'
import { apiMediaUrl } from '@/api/detect'
import { deleteHistory, deleteHistoryBatch, exportHistory, getHistory, listHistory, type HistoryDetail, type HistoryItem } from '@/api/history'

const rows = ref<HistoryItem[]>([])
const detail = ref<HistoryDetail | null>(null)
const drawer = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filters = reactive({ source_type: '', class_name: '', class_name_zh: '', username: '' })
const selectedRows = ref<HistoryItem[]>([])

function mediaUrl(path: string) { return apiMediaUrl(path) }
function videoThumbUrl(row: HistoryItem) { return row.video_thumb_url || row.result_url || row.original_url }
function filterParams() { return Object.fromEntries(Object.entries({ page: page.value, page_size: pageSize, ...filters }).filter(([, value]) => value !== '')) }
async function load() { const data = await listHistory(filterParams()); rows.value = data.items; total.value = data.total; selectedRows.value = [] }
function handleSelectionChange(selection: HistoryItem[]) { selectedRows.value = selection }
function formatParameters(detail: HistoryDetail | null) { if (!detail) return '-'; return `置信度 ${detail.confidence_threshold} / IoU ${detail.iou_threshold}` }
async function openDetail(row: HistoryItem) { detail.value = await getHistory(row.id); drawer.value = true }
async function remove(id: number) { try { await ElMessageBox.confirm('确认删除这条检测历史？', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteHistory(id); ElMessage.success('已删除'); await load() }
async function removeSelected() { if (!selectedRows.value.length) return; try { await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条？`, '批量删除', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteHistoryBatch(selectedRows.value.map((row) => row.id)); ElMessage.success('已批量删除'); await load() }
async function exportRows() { const response = await exportHistory(filterParams()); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = '检测历史.xlsx'; link.click(); URL.revokeObjectURL(url); ElMessage.success('已导出') }
onMounted(load)
</script>
