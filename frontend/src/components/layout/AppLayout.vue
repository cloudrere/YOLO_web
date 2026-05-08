<template>
  <div class="shell" :class="{ 'sidebar-collapsed': collapsed }">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div v-show="!collapsed">
          <strong>YOLO 视觉检测系统</strong>
          <span>智能检测工作台</span>
        </div>
      </div>

      <el-menu :default-active="activeMenuPath" router class="menu" :collapse="collapsed">
        <div class="menu-section-label" v-show="!collapsed">核心功能</div>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></el-icon>
          <span>数据总览</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></el-icon>
          <span>训练分析</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></el-icon>
          <span>智能检测</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></el-icon>
          <span>检测历史</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></el-icon>
          <span>模型管理</span>
        </el-menu-item>

        <div class="menu-section-label" v-show="!collapsed">系统管理</div>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></el-icon>
          <span>日志中心</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></el-icon>
          <span>系统维护</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">
          <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer" v-show="!collapsed">
        <span>运行模式</span>
        <strong>本地推理</strong>
        <small>{{ currentTime }}</small>
      </div>

      <button class="sidebar-toggle" @click="collapsed = !collapsed" :title="collapsed ? '展开菜单' : '收起菜单'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16">
          <polyline v-if="collapsed" points="9 18 15 12 9 6" />
          <polyline v-else points="15 18 9 12 15 6" />
        </svg>
      </button>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <span class="eyebrow dark">{{ breadcrumb }}</span>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="user-box glass-card compact">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="color: var(--color-primary)"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>{{ auth.user?.username }}</span>
          <el-button size="small" @click="logout">退出</el-button>
        </div>
      </header>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
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
.menu-section-label {
  padding: 16px 12px 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-tertiary);
  user-select: none;
}

.sidebar-toggle {
  position: absolute;
  bottom: 20px;
  right: -12px;
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: grid;
  place-items: center;
  padding: 0;
  z-index: 20;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}

.sidebar-toggle:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.sidebar-collapsed {
  --sidebar-width: 80px;
}

.sidebar-collapsed .sidebar {
  padding: 20px 12px;
}

.sidebar-collapsed .brand {
  justify-content: center;
  padding: 10px;
}

.sidebar-collapsed .brand-mark {
  margin: 0;
}

.sidebar-collapsed .menu .el-menu-item {
  justify-content: center;
  padding: 0 !important;
}

.sidebar-collapsed .menu .el-menu-item span {
  display: none;
}

.sidebar-collapsed .menu-section-label {
  display: none;
}

.sidebar-collapsed .sidebar-footer {
  display: none;
}

/* Element Plus menu collapse mode fix */
:deep(.el-menu--collapse) {
  width: auto;
}

:deep(.el-menu--collapse .el-menu-item) {
  justify-content: center;
}
</style>
