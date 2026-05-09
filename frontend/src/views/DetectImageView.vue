<template>
  <AppLayout>
    <!-- 检测工作台标题 + 模型状态 -->
    <section class="workstation-hero">
      <div>
        <h2>单图检测工作台</h2>
        <p>上传图片，配置检测参数，查看原图/检测图对比与结构化目标列表。</p>
      </div>
      <ModelStatusBar ref="modelBarRef" />
    </section>

    <!-- 三栏检测工作台 -->
    <section class="detection-workbench">
      <!-- 左栏：输入 + 参数 -->
      <DetectionParameterPanel
        ref="paramPanelRef"
        :confidence="params.confidence" :iou="params.iou" :save-history="params.save_history"
        :running="loading" :can-run="Boolean(imageFile) && !loading" run-label="开始检测"
        @run="runImage"
      >
        <template #extra-params>
          <div class="param-group">
            <label class="param-label" style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;">上传图片</label>
            <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage">
              <p style="font-size:13px;color:var(--color-muted);">拖拽或选择图片文件</p>
            </el-upload>
          </div>
        </template>
        <template #notes>
          <p class="text-muted" style="margin:0;">当前参数：置信度 {{ params.confidence.toFixed(2) }} / IoU {{ params.iou.toFixed(2) }} / {{ params.save_history ? '保存记录' : '仅本地检测' }}</p>
        </template>
      </DetectionParameterPanel>

      <!-- 中栏：检测画布 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex-between">
            <span style="font-weight:700;">检测画布</span>
            <el-tag :type="loading ? 'warning' : result ? 'success' : 'info'" size="small">
              {{ loading ? '推理中…' : result ? '完成' : '等待上传' }}
            </el-tag>
          </div>
        </template>
        <div class="detection-canvas" :class="{ 'has-result': result?.original_url || result?.result_url }">
          <div v-if="result?.original_url || result?.result_url" class="compare-grid" style="width:100%;">
            <figure v-if="result.original_url">
              <img :src="mediaUrl(result.original_url)" alt="原图" />
              <figcaption>原图</figcaption>
            </figure>
            <figure v-if="result.result_url">
              <img :src="mediaUrl(result.result_url)" alt="检测图" />
              <figcaption>检测图</figcaption>
            </figure>
          </div>
          <el-empty v-else :description="loading ? '正在推理，请稍候…' : '上传图片并点击检测按钮'" />
        </div>
        <!-- 快速指标 -->
        <div class="result-inspector-stats" style="margin-top:12px;">
          <div class="stat-item"><span class="stat-label">目标数</span><span class="stat-value">{{ result?.results.length ?? 0 }}</span></div>
          <div class="stat-item"><span class="stat-label">耗时</span><span class="stat-value">{{ result?.duration_ms ?? 0 }}ms</span></div>
          <div class="stat-item"><span class="stat-label">高频类别</span><span class="stat-value" style="font-size:14px;">{{ topClass }}</span></div>
          <div class="stat-item"><span class="stat-label">模型</span><span class="stat-value" style="font-size:13px;">{{ result?.model_name || '-' }}</span></div>
        </div>
        <p v-if="errorText" class="error-text" style="margin-top:8px;">{{ errorText }}</p>
      </el-card>

      <!-- 右栏：检测结果检查器 -->
      <DetectionResultInspector :results="result?.results || []" :duration="result?.duration_ms || 0" />
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import DetectionParameterPanel from '@/components/detection/DetectionParameterPanel.vue'
import DetectionResultInspector from '@/components/detection/DetectionResultInspector.vue'
import ModelStatusBar from '@/components/shared/ModelStatusBar.vue'
import { apiMediaUrl, detectImage, type ImageDetectResult } from '@/api/detect'

const modelBarRef = ref<InstanceType<typeof ModelStatusBar> | null>(null)
const paramPanelRef = ref<InstanceType<typeof DetectionParameterPanel> | null>(null)
const imageFile = ref<File | null>(null)
const result = ref<ImageDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })
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
  try {
    result.value = await detectImage(imageFile.value, { confidence: params.confidence, iou: params.iou, save_history: params.save_history })
    ElMessage.success('单图检测已完成')
    modelBarRef.value?.refresh()
  } catch (error: any) {
    errorText.value = error?.message || '检测失败'
    ElMessage.error(errorText.value)
  } finally { loading.value = false }
}
</script>
