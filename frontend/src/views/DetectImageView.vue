<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>单图检测工作站</h1>
        <p>上传图片 → 调节参数 → 查看对比图和结构化检测结果</p>
      </div>
      <div class="ws-tags">
        <el-tag size="small" type="success">独立页面</el-tag>
        <el-tag size="small" :type="params.save_history ? 'success' : 'warning'">{{ params.save_history ? '保存历史' : '仅本地' }}</el-tag>
      </div>
    </div>

    <div class="ws-workstation">
      <!-- 工具面板 -->
      <div class="ws-tool-panel">
        <div class="panel-label">检测参数</div>
        <div class="ws-param-group">
          <label>置信度 <span>{{ params.confidence.toFixed(2) }}</span></label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" />
        </div>
        <div class="ws-param-group">
          <label>IoU 阈值 <span>{{ params.iou.toFixed(2) }}</span></label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" />
        </div>
        <div class="ws-param-group">
          <el-switch v-model="params.save_history" active-text="保存历史" inactive-text="仅本地" />
        </div>
        <div class="ws-tool-divider"></div>
        <div class="panel-label">图片来源</div>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage">
          <p>选择一张图片</p>
        </el-upload>
        <div class="flex-gap" style="margin-top:10px">
          <el-button type="primary" :disabled="!imageFile || loading" :loading="loading" @click="runImage" style="flex:1">开始检测</el-button>
          <el-button :disabled="loading || !hasResult" @click="clearResults">清除</el-button>
        </div>
        <p v-if="errorText" class="text-danger" style="margin-top:8px">{{ errorText }}</p>
      </div>

      <!-- 预览舞台 -->
      <div class="ws-preview-stage">
        <div class="ws-preview-header">
          <span>{{ result ? '检测完成' : loading ? '推理中…' : '等待输入' }}</span>
          <el-tag size="small" :type="loading ? 'warning' : result ? 'success' : 'info'">{{ loading ? 'PROCESSING' : result ? 'DONE' : 'IDLE' }}</el-tag>
        </div>
        <div class="ws-preview-canvas">
          <template v-if="result?.original_url || result?.result_url">
            <div class="compare-split">
              <img v-if="result.original_url" :src="mediaUrl(result.original_url)" alt="原图" />
              <img v-if="result.result_url" :src="mediaUrl(result.result_url)" alt="检测图" />
            </div>
          </template>
          <span v-else style="color:var(--text-muted);font-size:13px">{{ loading ? '正在推理，请稍候…' : '上传图片后显示对比图' }}</span>
        </div>
        <div class="ws-preview-footer">
          <div class="foot-stat"><span class="stat-num">{{ result?.results.length ?? 0 }}</span><span class="stat-label">检测目标</span></div>
          <div class="foot-stat"><span class="stat-num">{{ result?.duration_ms ?? 0 }}</span><span class="stat-label">耗时 (ms)</span></div>
          <div class="foot-stat"><span class="stat-num">{{ topClass }}</span><span class="stat-label">高频类别</span></div>
        </div>
      </div>

      <!-- 结果面板 -->
      <div class="ws-result-panel">
        <div class="panel-label">检测结果</div>
        <template v-if="result?.results.length">
          <div class="ws-list">
            <div v-for="(item, idx) in result.results" :key="idx" class="ws-detection-row">
              <span class="det-class">{{ item.class_zh || item.class }}</span>
              <span class="det-conf">{{ (item.confidence * 100).toFixed(1) }}%</span>
              <span class="det-bbox">[{{ item.bbox.map(v => Math.round(v)).join(', ') }}]</span>
            </div>
          </div>
        </template>
        <el-empty v-else :description="loading ? '推理中…' : '检测完成后显示目标列表'" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiMediaUrl, detectImage, type ImageDetectResult } from '@/api/detect'

const imageFile = ref<File | null>(null)
const result = ref<ImageDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
const hasResult = computed(() => Boolean(result.value))
const topClass = computed(() => {
  const rows = result.value?.results || []
  if (!rows.length) return '-'
  const counts = rows.reduce<Record<string, { count: number; label: string }>>((acc, item) => {
    acc[item.class] = acc[item.class] || { count: 0, label: item.class_zh || item.class }
    acc[item.class].count += 1
    return acc
  }, {})
  return Object.values(counts).sort((a, b) => b.count - a.count)[0].label
})

function mediaUrl(path: string) { return apiMediaUrl(path) }
function selectImage(file: UploadFile) { imageFile.value = file.raw || null }
function removeImage() { imageFile.value = null }
async function runImage() {
  if (!imageFile.value) return
  loading.value = true; errorText.value = ''
  try { result.value = await detectImage(imageFile.value, { ...params }); ElMessage.success('检测完成') }
  catch (error: any) { errorText.value = error?.message || '检测失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false }
}
async function clearResults() {
  try { await ElMessageBox.confirm('确认清除当前检测结果吗？', '清除确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return }
  result.value = null; errorText.value = ''; ElMessage.success('结果已清除')
}
</script>
