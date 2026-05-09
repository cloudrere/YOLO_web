<template>
  <AppLayout>
    <!-- Hero 横幅：操作入口 -->
    <div class="workstation-hero">
      <div>
        <span class="eyebrow dark">检测历史追溯</span>
        <h2>动态检测结果中心</h2>
        <p>按来源、类别、用户与时间追溯检测记录，查看结构化检测框数据与智能分析。</p>
      </div>
      <div class="flex-wrap" style="gap:10px;">
        <el-button type="danger" :disabled="!selectedRows.length" @click="removeSelected" :icon="'Delete'">
          批量删除 {{ selectedRows.length ? `(${selectedRows.length})` : '' }}
        </el-button>
        <el-button @click="exportRows" :icon="'Download'">导出 Excel</el-button>
        <el-button @click="load" :icon="'Refresh'">刷新</el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="panel-card" style="padding:16px 20px;border-radius:var(--radius-md);background:var(--color-surface);border:1px solid var(--color-border);margin-bottom:var(--gap);">
      <el-form :inline="true" :model="filters" class="filter-bar" style="margin:0;">
        <el-form-item label="来源类型">
          <el-select v-model="filters.source_type" clearable placeholder="全部来源" style="width:150px;">
            <el-option label="单图" value="image" />
            <el-option label="批量图片" value="batch_image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="英文类别">
          <el-input v-model="filters.class_name" clearable placeholder="person / car" style="width:150px;" />
        </el-form-item>
        <el-form-item label="中文类别">
          <el-input v-model="filters.class_name_zh" clearable placeholder="人 / 汽车" style="width:140px;" />
        </el-form-item>
        <el-form-item label="用户">
          <el-input v-model="filters.username" clearable placeholder="用户名" style="width:130px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 检测历史表格 -->
    <div class="panel-card" style="padding:0;border-radius:var(--radius-md);background:var(--color-surface);border:1px solid var(--color-border);overflow:hidden;margin-bottom:var(--gap);">
      <div class="table-scroll history-table-shell">
        <el-table
          :data="rows"
          @row-click="openDetail"
          @selection-change="handleSelectionChange"
          style="width:100%;"
          empty-text="暂无检测历史记录"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column label="预览" width="180">
            <template #default="{ row }">
              <div class="thumb-pair" :class="{ 'video-thumb-pair': row.source_type === 'video' }">
                <template v-if="row.source_type === 'video'">
                  <div class="history-video-thumb" style="position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;border-radius:var(--radius-sm);background:#0f172a;">
                    <img
                      v-if="videoThumbUrl(row)"
                      :src="mediaUrl(videoThumbUrl(row))"
                      alt="视频首帧"
                      style="width:100%;height:100%;object-fit:cover;opacity:0.7;"
                    />
                    <button
                      class="thumb-play"
                      type="button"
                      @click.stop="openDetail(row)"
                      style="position:absolute;inset:0;display:grid;place-items:center;background:rgba(0,0,0,0.3);border:none;cursor:pointer;color:#fff;font-size:28px;"
                    >
                      &#9654;
                    </button>
                  </div>
                </template>
                <template v-else>
                  <img v-if="row.original_url" :src="mediaUrl(row.original_url)" alt="原图" style="width:72px;height:72px;object-fit:cover;border-radius:var(--radius-sm);" />
                  <img v-if="row.result_url" :src="mediaUrl(row.result_url)" alt="检测图" style="width:72px;height:72px;object-fit:cover;border-radius:var(--radius-sm);border:2px solid var(--color-primary-soft);" />
                </template>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="100">
            <template #default="{ row }">
              <el-tag :type="row.source_type === 'video' ? 'warning' : row.source_type === 'batch_image' ? 'info' : 'success'" size="small">
                {{ row.source_type === 'image' ? '单图' : row.source_type === 'batch_image' ? '批量' : '视频' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="用户" width="110" />
          <el-table-column prop="file_name" label="文件名" min-width="170" show-overflow-tooltip />
          <el-table-column label="识别类别" min-width="180">
            <template #default="{ row }">
              <div class="flex-wrap" style="gap:4px;">
                <el-tag
                  v-for="item in row.classes?.slice(0, 3)"
                  :key="`${item.class}-${item.class_zh}`"
                  class="tag"
                  size="small"
                  type="success"
                >
                  {{ item.class_zh || item.class }} {{ item.count }}
                </el-tag>
                <el-tag v-if="row.classes?.length > 3" size="small" type="info">+{{ row.classes.length - 3 }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : row.status || '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result_count" label="目标数" width="90" align="center" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="110" align="right" />
          <el-table-column prop="created_at_text" label="检测时间" width="180" />
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" plain @click.stop="remove(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div style="padding:16px 20px;display:flex;justify-content:flex-end;border-top:1px solid var(--color-border);">
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="pageSize"
          layout="prev, pager, next, total"
          @current-change="load"
          background
        />
      </div>
    </div>

    <!-- 详情抽屉 68% -->
    <el-drawer v-model="drawer" title="检测详情" size="68%">
      <template v-if="detail">
        <!-- 元数据网格 -->
        <div class="detail-meta-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">操作用户</span>
            <span class="metric-value" style="font-size:18px;">{{ detail.username || detail.user_id || '暂无' }}</span>
          </div>
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">推理模型</span>
            <span class="metric-value" style="font-size:18px;">{{ detail.model_name || '暂无' }}</span>
          </div>
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">运行设备</span>
            <span class="metric-value" style="font-size:18px;">{{ detail.device || '暂无' }}</span>
          </div>
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">检测时间</span>
            <span class="metric-value" style="font-size:18px;">{{ detail.created_at_text || detail.created_at }}</span>
          </div>
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">来源类型</span>
            <span class="metric-value" style="font-size:18px;">{{ detail.source_type === 'image' ? '单图' : detail.source_type === 'batch_image' ? '批量图片' : '视频' }}</span>
          </div>
          <div class="metric-card" style="padding:14px;">
            <span class="metric-label">检测参数</span>
            <span class="metric-value" style="font-size:18px;">{{ formatParameters(detail) }}</span>
          </div>
        </div>

        <!-- 视频播放器 -->
        <div v-if="detail?.source_type === 'video' && (detail.video_url || detail.video_stream_url)" class="history-video-player" style="margin-bottom:20px;">
          <div class="preview-header" style="margin-bottom:10px;">
            <span style="font-size:12px;color:var(--color-muted);">视频回放</span>
            <strong style="margin-left:8px;">{{ detail.video_url && !localVideoFailed ? '本地检测后视频' : '检测帧流' }}</strong>
          </div>
          <video
            v-if="detail.video_url && !localVideoFailed"
            :key="detail.id"
            class="history-local-video"
            :src="mediaUrl(detail.video_url)"
            controls
            preload="metadata"
            playsinline
            @error="handleVideoError"
            style="width:100%;max-height:420px;border-radius:var(--radius-md);background:#000;"
          />
          <img
            v-else-if="detail.video_stream_url"
            class="video-stream"
            :src="mediaUrl(detail.video_stream_url || '')"
            :alt="detail.file_name"
            style="width:100%;max-height:420px;object-fit:contain;border-radius:var(--radius-md);background:#000;"
          />
          <el-empty v-else description="暂无可播放视频" />
        </div>

        <!-- 原图 / 检测图对比 -->
        <div v-if="detail?.source_type !== 'video' && (detail?.original_url || detail?.result_url)" class="compare-grid history-preview" style="margin-bottom:20px;">
          <figure>
            <img v-if="detail.original_url" :src="mediaUrl(detail.original_url)" :alt="detail.file_name" style="background:#0f172a;" />
            <figcaption>原图</figcaption>
          </figure>
          <figure>
            <img v-if="detail.result_url" :src="mediaUrl(detail.result_url)" :alt="detail.file_name" style="background:#0f172a;" />
            <figcaption>检测图</figcaption>
          </figure>
        </div>

        <!-- 检测结果表格 -->
        <DetectionResultTable v-if="detail?.results?.length" :results="detail.results" />

        <!-- AI 分析 -->
        <AnalysisPanel v-if="detail?.analysis" :analysis="detail.analysis" />

        <!-- 可折叠 JSON -->
        <el-collapse v-if="detail" style="margin-top:16px;border-radius:var(--radius-md);overflow:hidden;">
          <el-collapse-item title="原始数据 (JSON)" name="raw">
            <pre class="json-box" style="margin:0;max-height:400px;">{{ JSON.stringify(detail, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </template>
      <el-empty v-else description="暂无检测详情" />
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

function mediaUrl(path: string) {
  return apiMediaUrl(path)
}
function videoThumbUrl(row: HistoryItem) {
  return row.video_thumb_url || row.result_url || row.original_url
}
function filterParams() {
  return Object.fromEntries(Object.entries({ page: page.value, page_size: pageSize, ...filters }).filter(([, value]) => value !== ''))
}
async function load() {
  const data = await listHistory(filterParams())
  rows.value = data.items
  total.value = data.total
  selectedRows.value = []
}
function handleSelectionChange(selection: HistoryItem[]) {
  selectedRows.value = selection
}
function formatParameters(detail: HistoryDetail | null) {
  if (!detail) return '-'
  return `置信度 ${detail.confidence_threshold} / IoU 阈值 ${detail.iou_threshold}`
}
async function openDetail(row: HistoryItem) {
  localVideoFailed.value = false
  detail.value = await getHistory(row.id)
  drawer.value = true
}
function handleVideoError() {
  localVideoFailed.value = true
  ElMessage.warning('本地视频暂不可直接播放，已切换为检测帧流')
}
async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这条检测历史吗？删除后不可在列表中恢复。', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteHistory(id)
  ElMessage.success('检测历史已删除')
  await load()
}
async function removeSelected() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条检测历史吗？删除后不可在列表中恢复。`, '批量删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteHistoryBatch(selectedRows.value.map((row) => row.id))
  ElMessage.success('检测历史已批量删除')
  await load()
}
async function exportRows() {
  const response = await exportHistory(filterParams())
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = '检测历史.xlsx'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('检测历史已导出')
}
onMounted(load)
</script>
