<template>
  <AppLayout>
    <div class="ws-card">
      <div class="ws-card-header">
        <span>实验记录库</span>
        <div class="flex-gap">
          <el-button size="small" type="danger" :disabled="!selectedRows.length" @click="removeSelected">批量删除</el-button>
          <el-button size="small" @click="exportRows">导出 Excel</el-button>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </div>
      <div class="ws-card-body">
        <div class="ws-filter-bar">
          <el-select v-model="filters.source_type" clearable placeholder="来源类型" style="width:130px">
            <el-option label="单图" value="image" />
            <el-option label="批量图片" value="batch_image" />
            <el-option label="视频" value="video" />
          </el-select>
          <el-input v-model="filters.class_name" clearable placeholder="英文类别" style="width:120px" />
          <el-input v-model="filters.class_name_zh" clearable placeholder="中文类别" style="width:120px" />
          <el-input v-model="filters.username" clearable placeholder="用户名" style="width:120px" />
          <el-button type="primary" size="small" @click="load">查询</el-button>
        </div>
        <el-table :data="rows" @row-click="openDetail" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="48" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="缩略图" width="180">
            <template #default="{ row }">
              <div class="thumb-pair" :class="{ 'video-thumb-pair': row.source_type === 'video' }">
                <template v-if="row.source_type === 'video'">
                  <div class="history-video-thumb">
                    <img v-if="videoThumbUrl(row)" :src="mediaUrl(videoThumbUrl(row))" alt="预览" />
                    <button class="thumb-play" type="button" @click.stop="openDetail(row)">播放</button>
                  </div>
                </template>
                <template v-else>
                  <img v-if="row.original_url" :src="mediaUrl(row.original_url)" alt="原图" />
                  <img v-if="row.result_url" :src="mediaUrl(row.result_url)" alt="检测图" />
                </template>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="120" />
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="file_name" label="文件名" min-width="180" />
          <el-table-column label="类别" min-width="180">
            <template #default="{ row }">
              <el-tag v-for="item in row.classes" :key="`${item.class}-${item.class_zh}`" class="tag" size="small" type="success">{{ item.class_zh || item.class }} {{ item.count }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="result_count" label="目标数" width="100" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="130" />
          <el-table-column prop="created_at_text" label="检测时间" width="190" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }"><el-button type="danger" size="small" @click.stop="remove(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
      </div>
    </div>

    <el-drawer v-model="drawer" title="检测详情" size="64%">
      <div v-if="detail" class="ws-info-grid" style="margin-bottom:10px">
        <div class="ws-info-item"><span class="info-label">用户</span><span class="info-value">{{ detail.username || detail.user_id || '-' }}</span></div>
        <div class="ws-info-item"><span class="info-label">模型</span><span class="info-value">{{ detail.model_name || '-' }}</span></div>
        <div class="ws-info-item"><span class="info-label">设备</span><span class="info-value">{{ detail.device || '-' }}</span></div>
        <div class="ws-info-item"><span class="info-label">检测时间</span><span class="info-value" style="font-size:10px">{{ detail.created_at_text || detail.created_at }}</span></div>
        <div class="ws-info-item"><span class="info-label">参数</span><span class="info-value" style="font-size:10px">{{ formatParameters(detail) }}</span></div>
      </div>
      <div v-if="detail?.source_type === 'video' && (detail.video_url || detail.video_stream_url)" style="margin-bottom:10px">
        <video v-if="detail.video_url && !localVideoFailed" :key="detail.id" style="width:100%;max-height:360px" :src="mediaUrl(detail.video_url)" controls preload="metadata" playsinline @error="handleVideoError"></video>
        <img v-else-if="detail.video_stream_url" class="video-stream" :src="mediaUrl(detail.video_stream_url || '')" :alt="detail.file_name" />
        <el-empty v-else description="暂无可播放视频" />
      </div>
      <div v-if="detail?.source_type !== 'video' && (detail?.original_url || detail?.result_url)" class="compare-split" style="aspect-ratio:2/1;background:#000;display:grid;grid-template-columns:1fr 1fr;margin-bottom:10px;border-radius:4px;overflow:hidden">
        <img v-if="detail.original_url" :src="mediaUrl(detail.original_url)" :alt="detail.file_name" style="width:100%;height:100%;object-fit:contain" />
        <img v-if="detail.result_url" :src="mediaUrl(detail.result_url)" :alt="detail.file_name" style="width:100%;height:100%;object-fit:contain;border-left:1px solid rgba(255,255,255,0.1)" />
      </div>
      <DetectionResultTable :results="detail?.results || []" />
      <AnalysisPanel v-if="detail?.analysis" :analysis="detail.analysis" />
      <pre v-if="detail" class="json-box">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'
import { apiMediaUrl } from '@/api/detect'
import { deleteHistory, deleteHistoryBatch, exportHistory, getHistory, listHistory, type HistoryDetail, type HistoryItem } from '@/api/history'

const rows = ref<HistoryItem[]>([])
const detail = ref<HistoryDetail | null>(null)
const drawer = ref(false)
const localVideoFailed = ref(false)
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
function formatParameters(detail: HistoryDetail | null) { if (!detail) return '-'; return `conf=${detail.confidence_threshold} / iou=${detail.iou_threshold}` }
async function openDetail(row: HistoryItem) { localVideoFailed.value = false; detail.value = await getHistory(row.id); drawer.value = true }
function handleVideoError() { localVideoFailed.value = true; ElMessage.warning('本地视频不可直接播放，已切换检为测帧流') }
async function remove(id: number) { try { await ElMessageBox.confirm('确认删除这条检测历史吗？', '删除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; await deleteHistory(id); ElMessage.success('已删除'); await load() }
async function removeSelected() { if (!selectedRows.value.length) return; try { await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条吗？`, '批量删除', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }; await deleteHistoryBatch(selectedRows.value.map((row) => row.id)); ElMessage.success('已批量删除'); await load() }
async function exportRows() { const response = await exportHistory(filterParams()); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = '实验记录.xlsx'; link.click(); URL.revokeObjectURL(url); ElMessage.success('已导出') }
onMounted(load)
</script>
