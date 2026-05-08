<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">检</div>
        <div>
          <strong>YOLO 视觉检测系统</strong>
          <span>智能检测工作台</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="menu">
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
      <div class="sidebar-footer">
        <span>运行模式</span>
        <strong>本地推理</strong>
        <small>{{ currentTime }}</small>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <span class="eyebrow dark">{{ breadcrumb }}</span>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="user-box glass-card compact">
          <span>{{ auth.user?.username }}</span>
          <el-button @click="logout">退出登录</el-button>
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
