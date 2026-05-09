<template>
  <div class="shell">
    <!-- 深色侧边栏 -->
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div class="brand-info">
          <strong>YOLO 工作站</strong>
          <span>视觉检测平台</span>
        </div>
      </div>

      <el-menu
        :default-active="activeMenuPath"
        router
        class="menu"
        background-color="transparent"
        text-color="#cbd5e1"
        active-text-color="#60a5fa"
      >
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">
          <span>指挥台</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">
          <span>训练分析</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">
          <span>启动检测</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">
          <span>检测历史</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">
          <span>模型中心</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">
          <span>系统日志</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">
          <span>系统维护</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">
          <span>AI 助手</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="footer-mode">
          <StatusPulse status="running" size="sm" />
          <strong>本地推理</strong>
        </div>
        <small>{{ currentTime }}</small>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
      <header class="topbar">
        <div class="topbar-meta">
          <span class="breadcrumb">{{ breadcrumb }}</span>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="user-box">
          <span class="username">{{ auth.user?.username }}</span>
          <el-button size="small" round @click="logout">退出登录</el-button>
        </div>
      </header>
      <div class="page-body">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import StatusPulse from '@/components/common/StatusPulse.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const currentTime = ref(formatCurrentTime())
let clockTimer: number | undefined
const pageMeta: Record<string, { title: string; subtitle: string; breadcrumb: string }> = {
  '/dashboard': { title: '数据总览', subtitle: '集中展示检测量、用户统计、系统资源与类别分布趋势。', breadcrumb: '总览' },
  '/training-analysis': { title: '训练分析', subtitle: '解析 YOLO results.csv，查看训练曲线、最终指标和 AI 诊断建议。', breadcrumb: '训练分析' },
  '/detect': { title: '智能检测', subtitle: '选择单图、批量、视频或实时流检测工作流，四个页面状态互不串扰。', breadcrumb: '检测' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片并查看原图、检测图和目标列表。', breadcrumb: '检测 / 单图' },
  '/detect/batch': { title: '批量图片检测', subtitle: '多图队列逐张检测，支持暂停、继续、结束和进度反馈。', breadcrumb: '检测 / 批量' },
  '/detect/video': { title: '视频文件检测', subtitle: '创建异步视频检测任务，查看帧流、进度和检测结果。', breadcrumb: '检测 / 视频' },
  '/detect/realtime': { title: '实时视频流检测', subtitle: '连接摄像头、RTSP 或 HTTP(S) 流，实时返回标注画面。', breadcrumb: '检测 / 实时' },
  '/history': { title: '检测历史', subtitle: '按来源、中文类别、用户与时间追溯检测记录和结构化框数据。', breadcrumb: '历史' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活 YOLO 模型并维护 GPU 与类别中文映射。', breadcrumb: '模型' },
  '/logs': { title: '日志中心', subtitle: '查看登录、检测、模型切换与任务执行日志，中文显示关键字段。', breadcrumb: '日志' },
  '/admin/users': { title: '用户管理', subtitle: '维护用户、角色、账号状态、最后登录时间和密码重置。', breadcrumb: '用户' },
  '/maintenance': { title: '系统维护', subtitle: '检查 GPU、模型、数据库、文件系统状态，并执行受控清理和初始化恢复。', breadcrumb: '维护' },
  '/assistant': { title: 'AI深度学习助手', subtitle: '接入 DeepSeek 或 OpenAI 兼容模型进行独立问答，不影响检测主流程。', breadcrumb: '助手' },
}
const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const activeMenuPath = computed(() => (route.path.startsWith('/detect') ? '/detect' : route.path))
const title = computed(() => meta.value.title)
const subtitle = computed(() => meta.value.subtitle)
const breadcrumb = computed(() => meta.value.breadcrumb)
function formatCurrentTime() {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}
onMounted(() => {
  clockTimer = window.setInterval(() => {
    currentTime.value = formatCurrentTime()
  }, 1000)
})
onUnmounted(() => {
  if (clockTimer) {
    window.clearInterval(clockTimer)
  }
})
function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ---- 侧边栏：深色科技风 ---- */
.sidebar {
  display: flex;
  flex-direction: column;
  width: 240px;
  min-width: 240px;
  height: 100vh;
  position: sticky;
  top: 0;
  padding: 20px 14px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #e2e8f0;
  overflow: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 18px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.06);
}

.brand-mark {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-weight: 900;
  font-size: 20px;
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
}

.brand-info strong {
  display: block;
  font-size: 14px;
  letter-spacing: -0.02em;
  color: #f1f5f9;
}

.brand-info span {
  display: block;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.menu {
  flex: 1;
  border-right: 0 !important;
  background: transparent !important;
  overflow-y: auto;
}

.menu .el-menu-item {
  height: 42px;
  margin: 3px 0;
  border-radius: var(--radius-md);
  color: #cbd5e1;
  font-size: 13px;
  transition: all var(--motion-fast) var(--ease-standard);
}

.menu .el-menu-item:hover {
  background: rgba(37, 99, 235, 0.12) !important;
  color: #93c5fd !important;
}

.menu .el-menu-item.is-active {
  background: rgba(37, 99, 235, 0.18) !important;
  color: #60a5fa !important;
  font-weight: 700;
}

.sidebar-footer {
  margin-top: auto;
  padding: 14px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.footer-mode {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-mode strong {
  color: #60a5fa;
  font-size: 13px;
}

.sidebar-footer small {
  display: block;
  margin-top: 8px;
  color: #64748b;
  font-size: 10px;
  font-family: var(--font-mono);
}

/* ---- 主内容区 ---- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar-meta .breadcrumb {
  display: block;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-soft);
  font-weight: 700;
  margin-bottom: 2px;
}

.topbar-meta h1 {
  font-size: 20px;
  font-weight: 800;
  margin: 0;
  color: var(--color-ink);
  letter-spacing: -0.02em;
}

.topbar-meta p {
  font-size: 12px;
  color: var(--color-muted);
  margin: 3px 0 0;
  max-width: 520px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 16px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  white-space: nowrap;
  flex-shrink: 0;
}

.username {
  font-weight: 700;
  color: var(--color-ink);
  font-size: 13px;
}

.page-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 28px;
}

.shell {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

/* 响应式 */
@media (max-width: 992px) {
  .sidebar {
    position: static;
    height: auto;
    width: 100%;
    min-width: 0;
  }
  .topbar {
    position: static;
    padding: 12px 16px;
  }
  .page-body {
    padding: 14px;
  }
}

@media (max-width: 768px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .page-body {
    padding: 10px;
  }
}
</style>
