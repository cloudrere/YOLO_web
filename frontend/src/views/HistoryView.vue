<template>
  <AppLayout>
    <el-card class="workstation-panel" shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700;">检测历史</span>
          <div style="display: flex; gap: 8px;">
            <el-button type="danger" size="small" :disabled="!selectedRows.length" @click="removeSelected">批量删除</el-button>
            <el-button size="small" @click="exportRows">导出 Excel</el-button>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </div>
      </template>
      <el-form :inline="true" :model="filters" class="filter-bar">
        <el-form-item label="来源类型">
          <el-select v-model="filters.source_type" clearable placeholder="全部" style="width: 150px;">
            <el-option label="单图" value="image" />
            <el-option label="批量图片" value="batch_image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="英文类别">
          <el-input v-model="filters.class_name" clearable placeholder="person / car" style="width: 150px;" />
        </el-form-item>
        <el-form-item label="中文类别">
          <el-input v-model="filters.class_name_zh" clearable placeholder="人 / 汽车" style="width: 150px;" />
        </el-form-item>
        <el-form-item label="用户">
          <el-input v-model="filters.username" clearable placeholder="用户名" style="width: 130px;" />
        </el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>
      <div class="table-scroll history-table-shell">
        <el-table :data="rows" @row-click="openDetail" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="48" />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="缩略图" width="170">
            <template #default="{ row }">
              <div class="thumb-pair" :class="{ 'video-thumb-pair': row.source_type === 'video' }">
                <template v-if="row.source_type === 'video'">
                  <div style="position: relative; overflow: hidden; min-height: 72px; border-radius: 6px; background: #1a202c;">
                    <img v-if="videoThumbUrl(row)" :src="mediaUrl(videoThumbUrl(row))" alt="视频第一帧" style="width: 100%; height: 72px; object-fit: cover;" />
                    <button type="button" @click.stop="openDetail(row)" style="position: absolute; inset: auto 6px 6px auto; border: 0; border-radius: 99px; padding: 3px 8px; background: #e89440; color: #fff; font-size: 11px; font-weight: 700; cursor: pointer;">播放</button>
                  </div>
                </template>
                <template v-else>
                  <img v-if="row.original_url" :src="mediaUrl(row.original_url)" alt="原图" />
                  <img v-if="row.result_url" :src="mediaUrl(row.result_url)" alt="检测图" />
                </template>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="110" />
          <el-table-column prop="username" label="用户" width="110" />
          <el-table-column prop="file_name" label="文件名" min-width="170" />
          <el-table-column label="类别" min-width="170">
            <template #default="{ row }">
              <el-tag v-for="item in row.classes" :key="`${item.class}-${item.class_zh}`" class="tag" type="success" size="small">
                {{ item.class_zh || item.class }} {{ item.count }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column prop="result_count" label="目标数" width="90" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
          <el-table-column prop="created_at_text" label="检测时间" width="180" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click.stop="remove(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="prev, pager, next, total" @current-change="load" />
    </el-card>

    <el-drawer v-model="drawer" title="检测详情" size="64%">
      <div v-if="detail" class="detail-meta-grid">
        <div><span>用户</span><strong>{{ detail.username || detail.user_id || '暂无' }}</strong></div>
        <div><span>模型</span><strong>{{ detail.model_name || '暂无' }}</strong></div>
        <div><span>设备</span><strong>{{ detail.device || '暂无' }}</strong></div>
        <div><span>检测时间</span><strong>{{ detail.created_at_text || detail.created_at }}</strong></div>
        <div><span>参数</span><strong>{{ formatParameters(detail) }}</strong></div>
        <div><span>来源</span><strong>{{ detail.source_type }}</strong></div>
      </div>
      <div v-if="detail?.source_type === 'video' && (detail.video_url || detail.video_stream_url)" class="history-video-player">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <span style="color: #e2e8f0; font-size: 14px; font-weight: 700;">视频回放</span>
          <span style="color: #a0aec0; font-size: 12px;">{{ detail.video_url && !localVideoFailed ? '本地视频' : '检测帧流' }}</span>
        </div>
        <video v-if="detail.video_url && !localVideoFailed" :key="detail.id" class="history-local-video" :src="mediaUrl(detail.video_url)" controls preload="metadata" playsinline @error="handleVideoError" style="width: 100%; max-height: 520px; border-radius: 10px;"></video>
        <img v-else-if="detail.video_stream_url" class="video-stream" :src="mediaUrl(detail.video_stream_url || '')" :alt="detail.file_name" style="max-height: 520px;" />
        <el-empty v-else description="暂无可播放视频" />
      </div>
      <div v-if="detail?.source_type !== 'video' && (detail?.original_url || detail?.result_url)" class="compare-grid history-preview" style="margin-bottom: 16px;">
        <figure><img v-if="detail.original_url" :src="mediaUrl(detail.original_url)" :alt="detail.file_name" /><figcaption>原图</figcaption></figure>
        <figure><img v-if="detail.result_url" :src="mediaUrl(detail.result_url)" :alt="detail.file_name" /><figcaption>检测图</figcaption></figure>
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
function formatParameters(detail: HistoryDetail | null) { if (!detail) return '-'; return `置信度 ${detail.confidence_threshold} / IoU ${detail.iou_threshold}` }
async function openDetail(row: HistoryItem) { localVideoFailed.value = false; detail.value = await getHistory(row.id); drawer.value = true }
function handleVideoError() { localVideoFailed.value = true; ElMessage.warning('本地视频暂不可直接播放，已切换为检测帧流') }
async function remove(id: number) { try { await ElMessageBox.confirm('确认删除这条检测历史吗？', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteHistory(id); ElMessage.success('已删除'); await load() }
async function removeSelected() { if (!selectedRows.value.length) return; try { await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条检测历史吗？`, '批量删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }) } catch { return }; await deleteHistoryBatch(selectedRows.value.map((row) => row.id)); ElMessage.success('已批量删除'); await load() }
async function exportRows() { const response = await exportHistory(filterParams()); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = '检测历史.xlsx'; link.click(); URL.revokeObjectURL(url); ElMessage.success('已导出') }
onMounted(load)
</script>
