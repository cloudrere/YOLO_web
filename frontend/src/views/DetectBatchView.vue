<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>批量图片检测</h2>
        <p>多张图片逐张处理，查看每张的检测结果</p>
      </div>
      <el-tag size="small">{{ params.confidence.toFixed(2) }} / {{ params.iou.toFixed(2) }}</el-tag>
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
          <el-upload drag multiple :auto-upload="false" :on-change="selectBatch" :on-remove="removeBatch">
            <p>拖拽或选择多张图片</p>
          </el-upload>
          <el-button type="primary" :disabled="!batchFiles.length || loading" :loading="loading" style="width:100%;margin-top:12px" @click="runBatch">开始检测</el-button>
          <p v-if="errorText" class="text-danger" style="margin-top:8px;font-size:12px">{{ errorText }}</p>
        </el-card>
      </div>

      <div class="workbench-preview">
        <div class="preview-header">
          <h3>{{ result ? '检测结果' : '预览区' }}</h3>
          <el-tag v-if="result" type="success" size="small">{{ result.items.length }} 张已处理</el-tag>
        </div>
        <div class="preview-canvas">
          <div v-if="result" class="thumb-grid" style="width:100%;height:100%;padding:12px;overflow-y:auto">
            <div v-for="(item, idx) in result.items" :key="idx" style="position:relative">
              <img v-if="item.result_url" :src="mediaUrl(item.result_url)" :alt="item.file_name" />
              <el-tag size="small" :type="item.status === 'success' ? 'success' : 'danger'" style="position:absolute;top:2px;right:2px">{{ item.status }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="上传图片后开始批量检测" :image-size="48" />
        </div>
        <div class="preview-stats">
          <div><strong>{{ result?.items.length ?? 0 }}</strong><span>已处理</span></div>
          <div><strong>{{ totalResults }}</strong><span>目标总数</span></div>
          <div><strong>{{ totalDuration }}ms</strong><span>总耗时</span></div>
        </div>
      </div>
    </div>

    <el-card v-if="result?.items.length" shadow="never">
      <template #header>检测结果列表</template>
      <div class="table-wrap">
        <el-table :data="result.items">
          <el-table-column prop="file_name" label="文件名" min-width="180" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }"><el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="results.length" label="目标数" width="100" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
          <el-table-column label="错误" min-width="200">
            <template #default="{ row }"><span class="text-danger">{{ row.error }}</span></template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, type UploadFile } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiMediaUrl, detectBatch } from '@/api/detect'
import type { BatchDetectResult } from '@/api/detect'

const batchFiles = ref<File[]>([])
const result = ref<BatchDetectResult | null>(null)
const loading = ref(false)
const errorText = ref('')
const params = reactive({ confidence: 0.25, iou: 0.7, save_history: true })

const totalResults = computed(() => result.value?.items.reduce((sum, item) => sum + (item.results?.length || 0), 0) ?? 0)
const totalDuration = computed(() => result.value?.items.reduce((sum, item) => sum + (item.duration_ms || 0), 0) ?? 0)

function mediaUrl(path: string) { return apiMediaUrl(path) }
function selectBatch(file: UploadFile) { if (file.raw) batchFiles.value.push(file.raw) }
function removeBatch() { batchFiles.value = [] }
async function runBatch() {
  if (!batchFiles.value.length) return
  loading.value = true; errorText.value = ''
  try { result.value = await detectBatch(batchFiles.value, { ...params }); ElMessage.success('批量检测完成') }
  catch (error: any) { errorText.value = error?.message || '批量检测失败'; ElMessage.error(errorText.value) }
  finally { loading.value = false }
}
</script>
