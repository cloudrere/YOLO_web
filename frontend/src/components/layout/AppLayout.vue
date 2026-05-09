<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div>
          <strong>YOLO 视觉工作站</strong>
          <span>Vision Workstation</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">
          <span class="menu-label">工作台首页</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">
          <span class="menu-label">训练分析</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">
          <span class="menu-label">智能检测</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">
          <span class="menu-label">检测历史</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">
          <span class="menu-label">模型管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">
          <span class="menu-label">日志中心</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">
          <span class="menu-label">用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">
          <span class="menu-label">系统维护</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">
          <span class="menu-label">AI 助手</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="status-dot"></div>
        <span>本地推理引擎</span>
        <small>{{ currentTime }}</small>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <span class="breadcrumb-text">{{ breadcrumb }}</span>
          <h1>{{ title }}</h1>
        </div>
        <div class="topbar-right">
          <span class="user-name">{{ auth.user?.username }}</span>
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
const currentTime = ref(formatCurrentTime())
let clockTimer: number | undefined

const pageMeta: Record<string, { title: string; breadcrumb: string }> = {
  '/dashboard': { title: '工作台首页', breadcrumb: '工作台 / 总览' },
  '/training-analysis': { title: '训练分析', breadcrumb: '工作台 / 训练分析' },
  '/detect': { title: '智能检测', breadcrumb: '检测 / 模式选择' },
  '/detect/image': { title: '单图检测', breadcrumb: '检测 / 单图分析' },
  '/detect/batch': { title: '批量检测', breadcrumb: '检测 / 批量处理' },
  '/detect/video': { title: '视频检测', breadcrumb: '检测 / 视频分析' },
  '/detect/realtime': { title: '实时流检测', breadcrumb: '检测 / 实时监控' },
  '/history': { title: '检测历史', breadcrumb: '历史 / 记录回溯' },
  '/models': { title: '模型管理', breadcrumb: '模型 / 模型库' },
  '/logs': { title: '日志中心', breadcrumb: '日志 / 系统日志' },
  '/admin/users': { title: '用户管理', breadcrumb: '管理 / 用户' },
  '/maintenance': { title: '系统维护', breadcrumb: '管理 / 维护' },
  '/assistant': { title: 'AI 助手', breadcrumb: '助手 / 智能问答' },
}

const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const activeMenuPath = computed(() => (route.path.startsWith('/detect') ? '/detect' : route.path))
const title = computed(() => meta.value.title)
const breadcrumb = computed(() => meta.value.breadcrumb)

function formatCurrentTime() {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  })
}

onMounted(() => {
  clockTimer = window.setInterval(() => { currentTime.value = formatCurrentTime() }, 1000)
})
onUnmounted(() => {
  if (clockTimer) window.clearInterval(clockTimer)
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.breadcrumb-text {
  font-size: 12px;
  color: var(--color-muted);
  letter-spacing: 0.04em;
}

.topbar-left { min-width: 0; }

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.user-name {
  color: var(--color-primary-deep);
  font-weight: 600;
  font-size: 14px;
}

.menu-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #48bb78;
  box-shadow: 0 0 8px rgba(72, 187, 120, 0.4);
  margin-bottom: 8px;
}
</style>
