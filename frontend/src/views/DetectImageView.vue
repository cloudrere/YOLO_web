<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>单图检测</h2>
        <p>上传图片查看原图、检测图和目标列表</p>
      </div>
      <el-tag :type="params.confidence >= 0.5 ? 'warning' : 'info'" size="small">置信度 {{ params.confidence.toFixed(2) }} / IoU {{ params.iou.toFixed(2) }}</el-tag>
    </div>

    <div class="workbench">
      <div class="workbench-controls">
        <el-card shadow="never">
          <template #header>检测参数</template>
          <label style="font-size:12px;color:#909399">置信度：{{ params.confidence.toFixed(2) }}</label>
          <el-slider v-model="params.confidence" :min="0.05" :max="0.95" :step="0.01" />
          <label style="font-size:12px;color:#909399">IoU 阈值：{{ params.iou.toFixed(2) }}</label>
          <el-slider v-model="params.iou" :min="0.05" :max="0.95" :step="0.01" />
          <el-switch v-model="params.save_history" active-text="上传到历史记录" inactive-text="仅本地检测" style="margin-top:8px" />
        </el-card>
        <el-card shadow="never">
          <template #header>上传图片</template>
          <el-upload drag :auto-upload="false" :limit="1" :on-change="selectImage" :on-remove="removeImage">
            <p>拖拽或选择图片文件</p>
          </el-upload>
          <el-button type="primary" :disabled="!imageFile || loading" :loading="loading" style="width:100%;margin-top:12px" @click="runDetect">开始检测</el-button>
          <p v-if="errorText" class="text-danger" style="margin-top:8px;font-size:12px">{{ errorText }}</p>
        </el-card>
      </div>

      <div class="workbench-preview">
        <div class="preview-header">
          <h3>{{ result ? '检测结果' : '预览区' }}</h3>
          <el-tag v-if="result" type="success" size="small">检测完成</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result" class="compare-grid" style="width:100%;height:100%;padding:12px">
            <figure><img v-if="result.original_url" :src="mediaUrl(result.original_url)" alt="原图" /><figcaption>原图</figcaption></figure>
            <figure><img v-if="result.result_url" :src="mediaUrl(result.result_url)" alt="检测图" /><figcaption>检测图</figcaption></figure>
          </div>
          <el-empty v-else description="上传图片后开始检测" :image-size="48" />
        </div>
        <div class="preview-stats">
          <div><strong>{{ result?.results?.length ?? 0 }}</strong><span>目标数</span></div>
          <div><strong>{{ result?.duration_ms ?? 0 }}ms</strong><span>耗时</span></div>
          <div><strong>{{ result?.model_name || '-' }}</strong><span>模型</span></div>
        </div>
      </div>
    </div>

    <el-card v-if="result?.results?.length" shadow="never">
      <template #header>检测目标列表</template>
      <div class="table-wrap">
        <el-table :data="result.results">
          <el-table-column prop="class" label="英文类别" width="160" />
          <el-table-column label="中文类别" width="160">
            <template #default="{ row }"><div class="class-pair"><span>{{ row.class_zh || '-' }}</span></div></template>
          </el-table-column>
          <el-table-column label="置信度" width="130">
            <template #default="{ row }"><span class="confidence-cell">{{ formatConfidence(row.confidence) }}</span></template>
          </el-table-column>
          <el-table-column label="边界框" min-width="200">
            <template #default="{ row }">x1:{{ row.bbox[0] }} y1:{{ row.bbox[1] }} x2:{{ row.bbox[2] }} y2:{{ row.bbox[3] }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiMediaUrl, detectImage } from '@/api/detect'
import type { ImageDetectResult } from '@/api/detect'

const imageFile = ref<File | null>(null)
const result = ref<ImageDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })

function mediaUrl(path: string) { return apiMediaUrl(path) }
function formatConfidence(value?: number | null) { return value === null || value === undefined ? '-' : `${(Number(value) * 100).toFixed(1)}%` }
function selectImage(file: UploadFile) { imageFile.value = file.raw || null }
function removeImage() { imageFile.value = null }
async function runDetect() {
  if (!imageFile.value) return
  loading.value = true; errorText.value = ''
  try { result.value = await detectImage(imageFile.value, { confidence: params.confidence, iou: params.iou, save_history: params.save_history }); ElMessage.success('检测完成') }
  catch (error: any) { errorText.value = error?.message || '检测失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false }
}
</script>
