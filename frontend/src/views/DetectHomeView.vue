<template>
  <AppLayout>
    <section class="detect-home-hero">
      <div>
        <span class="eyebrow dark">检测工作区</span>
        <h2>选择检测模式</h2>
        <p>四种检测模式提供独立的工作区，参数、任务和结果互不干扰。选择最适合你当前任务的模式开始工作。</p>
      </div>
      <div class="detect-status-sidebar">
        <div class="detect-home-status">
          <div><span>可用模式</span><strong>4 种</strong></div>
          <div><span>独立工作区</span><strong>隔离运行</strong></div>
          <div><span>当前模型</span><strong>本地推理</strong></div>
        </div>
      </div>
    </section>

    <section class="detect-mode-grid">
      <RouterLink v-for="item in modes" :key="item.path" :to="item.path" class="detect-mode-card">
        <div class="detect-mode-icon">{{ item.icon }}</div>
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>
        <div class="mode-card-footer">
          <el-tag size="small">{{ item.tag }}</el-tag>
          <span>进入 →</span>
        </div>
      </RouterLink>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const modes = [
  { path: '/detect/image', icon: '🖼', title: '单图检测', description: '上传单张图片进行目标检测，对比原图与标注结果，查看结构化检测数据。', tag: '快速验证' },
  { path: '/detect/batch', icon: '📦', title: '批量检测', description: '多张图片队列处理，支持暂停继续和结束控制，逐张返回检测结果。', tag: '批量任务' },
  { path: '/detect/video', icon: '🎬', title: '视频检测', description: '上传视频文件创建异步任务，实时查看标注帧流和检测进度。', tag: '异步抽帧' },
  { path: '/detect/realtime', icon: '📡', title: '实时流检测', description: '连接摄像头或 RTSP/HTTP 流媒体，实时显示 YOLO 标注画面。', tag: 'MJPEG 实时' },
]
</script>

<style scoped>
.detect-status-sidebar {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.detect-home-status {
  display: grid;
  gap: 10px;
}

.detect-home-status div {
  padding: 14px 16px;
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  background: var(--color-surface);
}

.detect-home-status span { display: block; color: var(--color-muted); font-size: 11px; }
.detect-home-status strong { display: block; margin-top: 4px; color: var(--color-primary-deep); font-size: 16px; }
</style>
