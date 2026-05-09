<template>
  <div class="evidence-panel">
    <!-- 原图/检测图对比 -->
    <div v-if="detail?.source_type !== 'video' && (detail?.original_url || detail?.result_url)" class="compare-grid">
      <figure v-if="detail.original_url">
        <img :src="mediaUrl(detail.original_url)" alt="原图" />
        <figcaption>原图</figcaption>
      </figure>
      <figure v-if="detail.result_url">
        <img :src="mediaUrl(detail.result_url)" alt="检测图" />
        <figcaption>检测图</figcaption>
      </figure>
    </div>

    <!-- 视频 -->
    <div v-if="detail?.source_type === 'video' && (detail.video_url || detail.video_stream_url)" style="margin-bottom:var(--gap);">
      <video v-if="detail.video_url && !videoFailed" :key="detail.id" class="video-player" :src="mediaUrl(detail.video_url)" controls preload="metadata" @error="videoFailed = true" />
      <img v-else-if="detail.video_stream_url" class="video-stream" :src="mediaUrl(detail.video_stream_url)" alt="帧流" />
    </div>

    <!-- 检测结果表 -->
    <DetectionResultTable v-if="detail?.results?.length" :results="detail.results" />

    <!-- AI 分析 -->
    <AnalysisPanel v-if="detail?.analysis" :analysis="detail.analysis" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { HistoryDetail } from '@/api/history'
import { apiMediaUrl } from '@/api/detect'
import AnalysisPanel from '@/components/detection/AnalysisPanel.vue'
import DetectionResultTable from '@/components/detection/DetectionResultTable.vue'

defineProps<{ detail: HistoryDetail | null }>()

const videoFailed = ref(false)
function mediaUrl(path: string) { return apiMediaUrl(path) }
</script>
