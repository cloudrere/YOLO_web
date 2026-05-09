<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="app-sidebar-brand">
        <div class="brand-icon">Y</div>
        <div class="brand-text">
          <strong>YOLO 检测系统</strong>
          <span>智能检测工作台</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="app-sidebar-menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">数据总览</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">训练分析</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">智能检测</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">检测历史</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">模型管理</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">日志中心</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">用户管理</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">系统维护</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">AI 助手</el-menu-item>
      </el-menu>
      <div class="app-sidebar-footer">
        <span>运行模式</span>
        <strong>本地推理</strong>
        <small>{{ currentTime }}</small>
      </div>
    </aside>
    <main class="app-main">
      <header class="app-topbar">
        <div class="app-topbar-left">
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="app-topbar-right">
          <span style="font-size:13px;color:#909399">{{ auth.user?.username }}</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </header>
      <div class="app-content">
        <slot />
      </div>
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
const pageMeta: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: '数据总览', subtitle: '检测量、用户统计、系统资源与类别分布趋势' },
  '/training-analysis': { title: '训练分析', subtitle: 'YOLO results.csv 训练曲线与 AI 诊断' },
  '/detect': { title: '智能检测', subtitle: '单图、批量、视频或实时流检测工作流' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片查看检测结果' },
  '/detect/batch': { title: '批量图片检测', subtitle: '多图队列逐张检测' },
  '/detect/video': { title: '视频文件检测', subtitle: '异步视频抽帧检测任务' },
  '/detect/realtime': { title: '实时视频流检测', subtitle: '摄像头、RTSP 或 HTTP 流实时标注' },
  '/history': { title: '检测历史', subtitle: '按来源、类别、用户追溯检测记录' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活模型与 GPU 切换' },
  '/logs': { title: '日志中心', subtitle: '系统登录、检测、任务执行日志' },
  '/admin/users': { title: '用户管理', subtitle: '用户、角色、账号状态与密码重置' },
  '/maintenance': { title: '系统维护', subtitle: 'GPU、模型、数据库状态与清理操作' },
  '/assistant': { title: 'AI 助手', subtitle: 'DeepSeek / OpenAI 问答' },
}
const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const activeMenuPath = computed(() => (route.path.startsWith('/detect') ? '/detect' : route.path))
const title = computed(() => meta.value.title)
const subtitle = computed(() => meta.value.subtitle)
function formatCurrentTime() {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  })
}
onMounted(() => { clockTimer = window.setInterval(() => { currentTime.value = formatCurrentTime() }, 1000) })
onUnmounted(() => { if (clockTimer) window.clearInterval(clockTimer) })
function logout() { auth.logout(); router.push('/login') }
</script>
