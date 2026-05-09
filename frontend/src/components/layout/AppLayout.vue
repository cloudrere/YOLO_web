<template>
  <div class="ops-shell">
    <aside class="ops-sidebar">
      <div class="ops-sidebar-brand">
        <div class="brand-dot"></div>
        <div>
          <strong>YOLO 视觉检测系统</strong>
          <span>运维管理平台</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="ops-sidebar-menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据总览</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>训练分析</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">
          <el-icon><Aim /></el-icon>
          <span>智能检测</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">
          <el-icon><Timer /></el-icon>
          <span>检测历史</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">
          <el-icon><Setting /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">
          <el-icon><Document /></el-icon>
          <span>日志中心</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">
          <el-icon><Tools /></el-icon>
          <span>系统维护</span>
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
      </el-menu>
      <div class="ops-sidebar-footer">
        <strong>本地推理 · 运行中</strong>
        <span>{{ currentTime }}</span>
      </div>
    </aside>
    <div class="ops-main">
      <header class="ops-topbar">
        <div class="ops-topbar-left">
          <span class="breadcrumb">{{ breadcrumb }}</span>
          <span class="breadcrumb-sep">/</span>
          <h1>{{ title }}</h1>
        </div>
        <div class="ops-topbar-right">
          <el-tag size="small">{{ auth.user?.username }}</el-tag>
          <el-button size="small" @click="logout">退出</el-button>
        </div>
      </header>
      <div class="ops-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Aim,
  ChatDotRound,
  DataAnalysis,
  Document,
  Setting,
  Timer,
  Tools,
  TrendCharts,
  User,
} from '@element-plus/icons-vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const currentTime = ref(formatCurrentTime())
let clockTimer: number | undefined

const pageMeta: Record<string, { title: string; subtitle: string; breadcrumb: string }> = {
  '/dashboard': { title: '数据总览', subtitle: '检测量、用户统计、系统资源与类别分布趋势。', breadcrumb: '总览' },
  '/training-analysis': { title: '训练分析', subtitle: '解析 YOLO results.csv，查看训练曲线与 AI 诊断。', breadcrumb: '训练分析' },
  '/detect': { title: '智能检测', subtitle: '单图、批量、视频或实时流检测，状态互不串扰。', breadcrumb: '检测' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片并查看原图、检测图和目标列表。', breadcrumb: '检测 / 单图' },
  '/detect/batch': { title: '批量图片检测', subtitle: '多图队列逐张检测，支持暂停、继续、进度反馈。', breadcrumb: '检测 / 批量' },
  '/detect/video': { title: '视频文件检测', subtitle: '创建异步视频检测任务，查看帧流与进度。', breadcrumb: '检测 / 视频' },
  '/detect/realtime': { title: '实时视频流检测', subtitle: '连接摄像头、RTSP 或 HTTP(S) 流实时标注。', breadcrumb: '检测 / 实时' },
  '/history': { title: '检测历史', subtitle: '按来源、类别、用户与时间追溯检测记录。', breadcrumb: '历史' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活模型，维护 GPU 与类别映射。', breadcrumb: '模型' },
  '/logs': { title: '日志中心', subtitle: '查看登录、检测、模型切换与任务执行日志。', breadcrumb: '日志' },
  '/admin/users': { title: '用户管理', subtitle: '维护用户、角色、账号状态和密码重置。', breadcrumb: '用户' },
  '/maintenance': { title: '系统维护', subtitle: '检查 GPU、模型、数据库状态，执行清理与恢复。', breadcrumb: '维护' },
  '/assistant': { title: 'AI深度学习助手', subtitle: '接入 DeepSeek 或 OpenAI 兼容模型独立问答。', breadcrumb: '助手' },
}

const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const activeMenuPath = computed(() => (route.path.startsWith('/detect') ? '/detect' : route.path))
const title = computed(() => meta.value.title)
const subtitle = computed(() => meta.value.subtitle)
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
