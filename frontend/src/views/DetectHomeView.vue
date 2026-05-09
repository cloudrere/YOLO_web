<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>选择检测工作流</h1>
        <p>四种检测模式独立页面，参数、任务、预览和结果互不串扰。</p>
      </div>
      <el-tag size="small" type="success">独立状态</el-tag>
    </div>

    <div class="ws-mode-grid">
      <RouterLink v-for="item in modes" :key="item.path" :to="item.path" class="ws-mode-card">
        <span class="mode-kicker">{{ item.kicker }}</span>
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>
        <div class="mode-foot">
          <el-tag size="small">{{ item.tag }}</el-tag>
          <span style="font-size:12px;color:var(--accent);font-weight:600">进入 →</span>
        </div>
      </RouterLink>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const modes = [
  { path: '/detect/image', kicker: 'IMAGE', title: '单图检测', description: '上传一张图片，参数调节 → 查看原图/检测图/目标表。', tag: '快速验证' },
  { path: '/detect/batch', kicker: 'BATCH', title: '批量图片检测', description: '多张图片逐张处理，支持暂停、继续、结束和进度反馈。', tag: '批量任务' },
  { path: '/detect/video', kicker: 'VIDEO', title: '视频文件检测', description: '上传视频创建异步任务，查看帧流、进度和检测结果。', tag: '异步抽帧' },
  { path: '/detect/realtime', kicker: 'LIVE', title: '实时视频流检测', description: '连接摄像头或 RTSP/HTTP 流，实时显示 YOLO 标注画面。', tag: 'MJPEG 实时' },
]
</script>
