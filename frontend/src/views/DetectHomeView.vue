<template>
  <AppLayout>
    <AnimatedPage>
      <!-- Hero 横幅 - 内嵌模型状态条 -->
      <section class="workstation-hero detect-hero">
        <div class="hero-info">
          <span class="hero-eyebrow">检测模式启动舱</span>
          <h2>选择独立检测工作流</h2>
          <p>四种检测模式拆分为独立页面，参数、任务、预览和结果互不串扰。</p>
        </div>
        <div class="hero-model">
          <ActiveModelBanner ref="modelBannerRef" />
        </div>
      </section>

      <!-- 四张检测模式卡片 -->
      <section class="detect-mode-grid">
        <MotionPanel v-for="item in modes" :key="item.path" effect="shimmer">
          <RouterLink :to="item.path" class="mode-card">
            <div class="mode-icon">
              <span class="mode-emoji">{{
                item.kicker === 'IMAGE' ? '\u{1F5BC}' : item.kicker === 'BATCH' ? '\u{1F4DA}' : item.kicker === 'VIDEO' ? '\u{1F3AC}' : '\u{1F4E1}'
              }}</span>
            </div>
            <div class="mode-body">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </div>
            <div class="mode-footer">
              <el-tag size="small" round>{{ item.tag }}</el-tag>
              <span class="mode-enter">
                进入检测
                <span class="mode-arrow">&rarr;</span>
              </span>
            </div>
          </RouterLink>
        </MotionPanel>
      </section>

      <!-- 系统就绪状态面板 -->
      <section class="readiness-section">
        <el-card shadow="never">
          <template #header>
            <div class="card-header-row">
              <span class="panel-title">系统就绪状态</span>
              <StatusPulse
                :status="(modelBannerRef?.active?.warmup_status === 'cuda_ready' || modelBannerRef?.active?.warmup_status === 'cpu_ready') ? 'success' : modelBannerRef?.active?.warmup_status === 'failed' ? 'danger' : modelBannerRef?.active?.warmup_status === 'pending' ? 'warning' : 'idle'"
                size="sm"
              />
            </div>
          </template>
          <div class="readiness-grid">
            <div class="readiness-item">
              <span class="readiness-label">推理模型</span>
              <strong>{{ modelBannerRef?.active?.active_model?.display_name || modelBannerRef?.active?.active_model?.name || '未激活' }}</strong>
            </div>
            <div class="readiness-item">
              <span class="readiness-label">推理设备</span>
              <strong>
                <template v-if="modelBannerRef?.active?.device === 'cpu' || modelBannerRef?.active?.requested_device === 'cpu'">CPU</template>
                <template v-else-if="modelBannerRef?.active?.device?.startsWith('cuda') || modelBannerRef?.active?.requested_device?.startsWith('cuda')">GPU (CUDA)</template>
                <template v-else>自动选择</template>
              </strong>
            </div>
            <div class="readiness-item">
              <span class="readiness-label">预热状态</span>
              <strong>
                <el-tag
                  :type="(modelBannerRef?.active?.warmup_status === 'cuda_ready' || modelBannerRef?.active?.warmup_status === 'cpu_ready') ? 'success' : modelBannerRef?.active?.warmup_status === 'failed' ? 'danger' : modelBannerRef?.active?.warmup_status === 'pending' ? 'warning' : 'info'"
                  size="small"
                >{{
                  { cuda_ready: 'GPU 就绪', cpu_ready: 'CPU 就绪', pending: '预热中', failed: '预热失败', not_loaded: '未加载', idle: '待初始化' }[modelBannerRef?.active?.warmup_status || ''] || '未知'
                }}</el-tag>
              </strong>
            </div>
            <div class="readiness-item">
              <span class="readiness-label">CUDA 可用</span>
              <strong>
                <template v-if="modelBannerRef?.active?.device?.startsWith('cuda') || modelBannerRef?.active?.requested_device?.startsWith('cuda')">
                  <span class="text-success">是</span>
                </template>
                <template v-else-if="!modelBannerRef?.active">
                  <span class="text-muted">检测中</span>
                </template>
                <template v-else>
                  <span class="text-warning">否 (CPU 模式)</span>
                </template>
              </strong>
            </div>
          </div>
        </el-card>
      </section>
    </AnimatedPage>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import ActiveModelBanner from '@/components/model/ActiveModelBanner.vue'
import MotionPanel from '@/components/common/MotionPanel.vue'
import AnimatedPage from '@/components/common/AnimatedPage.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'

const modelBannerRef = ref<InstanceType<typeof ActiveModelBanner> | null>(null)

const modes = [
  { path: '/detect/image', kicker: 'IMAGE', title: '单图检测', description: '上传一张图片，查看原图、检测图和目标列表。', tag: '快速验证' },
  { path: '/detect/batch', kicker: 'BATCH', title: '批量图片检测', description: '多张图片逐张处理，支持暂停、继续、结束和进度反馈。', tag: '批量任务' },
  { path: '/detect/video', kicker: 'VIDEO', title: '视频文件检测', description: '上传视频创建异步任务，持续查看帧流、进度和检测结果。', tag: '异步抽帧' },
  { path: '/detect/realtime', kicker: 'LIVE', title: '实时视频流检测', description: '连接摄像头或 RTSP/HTTP 流，实时显示 YOLO 标注画面。', tag: 'MJPEG 实时' },
]
</script>

<style scoped>
/* Hero 横幅专用 */
.detect-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 50%, #ecfeff 100%);
  border: 1px solid #bfdbfe;
  position: relative;
  overflow: hidden;
}

.detect-hero::before {
  content: "";
  position: absolute;
  bottom: -60%;
  left: -10%;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.hero-info .hero-eyebrow {
  display: inline-block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  font-weight: 700;
  margin-bottom: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
}

.hero-model {
  flex-shrink: 0;
  min-width: 320px;
}

/* 检测模式卡片 */
.mode-card {
  display: flex;
  flex-direction: column;
  padding: 24px;
  min-height: 220px;
  text-decoration: none;
  color: inherit;
  position: relative;
  z-index: 1;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  transition: all var(--motion-normal) var(--ease-standard);
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.mode-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  margin-bottom: 16px;
  transition: transform var(--motion-fast) var(--ease-standard);
}

.mode-card:hover .mode-icon {
  transform: scale(1.08);
}

.mode-card:nth-child(1) .mode-icon { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
.mode-card:nth-child(2) .mode-icon { background: linear-gradient(135deg, #7c3aed, #6d28d9); }
.mode-card:nth-child(3) .mode-icon { background: linear-gradient(135deg, #ea580c, #c2410c); }
.mode-card:nth-child(4) .mode-icon { background: linear-gradient(135deg, #0891b2, #0e7490); }

.mode-card:nth-child(1):hover { border-color: rgba(37, 99, 235, 0.4); }
.mode-card:nth-child(2):hover { border-color: rgba(124, 58, 237, 0.4); }
.mode-card:nth-child(3):hover { border-color: rgba(234, 88, 12, 0.4); }
.mode-card:nth-child(4):hover { border-color: rgba(8, 145, 178, 0.4); }

.mode-emoji {
  font-size: 22px;
  line-height: 1;
}

.mode-body {
  flex: 1;
}

.mode-body h3 {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--color-ink);
}

.mode-body p {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
  line-height: 1.6;
}

.mode-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.mode-enter {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.mode-arrow {
  transition: transform var(--motion-fast) var(--ease-standard);
}

.mode-card:hover .mode-arrow {
  transform: translateX(4px);
}

/* 系统就绪状态面板 */
.readiness-section {
  margin-top: var(--gap);
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-ink);
}

.readiness-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--gap);
}

.readiness-item {
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  transition: border-color var(--motion-fast), box-shadow var(--motion-fast);
}

.readiness-item:hover {
  border-color: var(--color-primary-light);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
}

.readiness-label {
  display: block;
  font-size: 11px;
  color: var(--color-soft);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.readiness-item strong {
  display: block;
  font-size: 15px;
  color: var(--color-ink);
  font-weight: 700;
}

.text-success {
  color: var(--color-success) !important;
}

.text-warning {
  color: var(--color-warning) !important;
}

.text-muted {
  color: var(--color-soft) !important;
}

/* 响应式 */
@media (max-width: 1400px) {
  .readiness-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 992px) {
  .detect-hero {
    flex-direction: column;
  }
  .hero-model {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .readiness-grid {
    grid-template-columns: 1fr;
  }
}
</style>
