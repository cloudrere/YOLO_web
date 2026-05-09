<template>
  <div class="detect-canvas" :class="{ 'has-image': src }">
    <img v-if="src" :src="src" alt="检测画布" />
    <DetectionScanOverlay v-if="scanning" />
    <DetectionBoxOverlay v-if="boxes?.length" :boxes="boxes" />
    <EmptyDetectionCanvas v-if="!src && !scanning" :title="emptyTitle" :desc="emptyDesc" />
  </div>
</template>

<script setup lang="ts">
import DetectionScanOverlay from './DetectionScanOverlay.vue'
import DetectionBoxOverlay from './DetectionBoxOverlay.vue'
import EmptyDetectionCanvas from '../common/EmptyDetectionCanvas.vue'

defineProps<{
  src?: string
  scanning?: boolean
  boxes?: Array<{ x: number; y: number; w: number; h: number; label: string; confidence: number }>
  emptyTitle?: string
  emptyDesc?: string
}>()
</script>
