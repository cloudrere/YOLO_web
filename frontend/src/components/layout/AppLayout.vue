<template>
  <div class="ws-shell">
    <aside class="ws-sidebar">
      <div class="ws-brand">
        <div class="brand-icon">Y</div>
        <div class="brand-text">
          <strong>YOLO Vision</strong>
          <span>视觉实验工作站</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="ws-nav">
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
      <div class="ws-sidebar-footer">
        <strong>本地推理 · 运行中</strong>
        <span>{{ currentTime }}</span>
      </div>
    </aside>
    <div class="ws-main">
      <header class="ws-topbar">
        <div class="ws-topbar-left">
          <span class="path-sep">{{ breadcrumb }}</span>
        </div>
        <div class="ws-topbar-right">
          <span style="color:var(--text-secondary);font-size:11px">{{ auth.user?.username }}</span>
          <el-button size="small" @click="logout">退出</el-button>
        </div>
      </header>
      <div class="ws-content">
        <slot />
      </div>
    </div>
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
  '/dashboard': { title: '数据总览', subtitle: '检测量、用户统计、系统资源与类别分布。', breadcrumb: 'Workspace / 总览' },
  '/training-analysis': { title: '训练分析', subtitle: 'YOLO results.csv 训练曲线与 AI 诊断。', breadcrumb: 'Workspace / 训练分析' },
  '/detect': { title: '智能检测', subtitle: '单图、批量、视频、实时流四种独立工作流。', breadcrumb: 'Workspace / 检测' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片 → 参数调节 → 查看原图/检测图/目标表。', breadcrumb: 'Workspace / 检测 / 单图' },
  '/detect/batch': { title: '批量图片检测', subtitle: '队列逐张处理，暂停/继续/结束，进度实时反馈。', breadcrumb: 'Workspace / 检测 / 批量' },
  '/detect/video': { title: '视频文件检测', subtitle: '异步视频任务，帧流、进度、结果独立轮询。', breadcrumb: 'Workspace / 检测 / 视频' },
  '/detect/realtime': { title: '实时视频流检测', subtitle: '摄像头/RTSP/HTTP 流实时标注 MJPEG 输出。', breadcrumb: 'Workspace / 检测 / 实时' },
  '/history': { title: '检测历史', subtitle: '按来源、类别、用户、时间追溯实验记录。', breadcrumb: 'Workspace / 历史' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活 YOLO 模型及类别中文映射。', breadcrumb: 'Workspace / 模型' },
  '/logs': { title: '日志中心', subtitle: '登录、检测、模型、任务执行日志检索。', breadcrumb: 'Workspace / 日志' },
  '/admin/users': { title: '用户管理', subtitle: '用户、角色、账号状态与密码维护。', breadcrumb: 'Workspace / 用户' },
  '/maintenance': { title: '系统维护', subtitle: 'GPU、模型、数据库、文件系统诊断与维护。', breadcrumb: 'Workspace / 维护' },
  '/assistant': { title: 'AI深度学习助手', subtitle: '接入 DeepSeek/OpenAI 兼容模型独立问答。', breadcrumb: 'Workspace / 助手' },
}

const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const activeMenuPath = computed(() => (route.path.startsWith('/detect') ? '/detect' : route.path))
const breadcrumb = computed(() => meta.value.breadcrumb)

function formatCurrentTime() {
  return new Date().toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}
onMounted(() => { clockTimer = window.setInterval(() => { currentTime.value = formatCurrentTime() }, 1000) })
onUnmounted(() => { if (clockTimer) window.clearInterval(clockTimer) })
function logout() { auth.logout(); router.push('/login') }
</script>
