<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div>
          <strong>YOLO 视觉检测</strong>
          <span>安防监控中心</span>
        </div>
      </div>
      <el-menu :default-active="activeMenuPath" router class="menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">
          <span class="menu-icon">&#9632;</span> 监控总览
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/training-analysis">
          <span class="menu-icon">&#9632;</span> 训练分析
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">
          <span class="menu-icon">&#9632;</span> 智能检测
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">
          <span class="menu-icon">&#9632;</span> 事件档案
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">
          <span class="menu-icon">&#9632;</span> 模型管理
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">
          <span class="menu-icon">&#9632;</span> 审计日志
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">
          <span class="menu-icon">&#9632;</span> 用户管理
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">
          <span class="menu-icon">&#9632;</span> 系统维护
        </el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">
          <span class="menu-icon">&#9632;</span> 运维助手
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <span>系统状态</span>
        <strong>运行中</strong>
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
        <div class="user-box compact">
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
const currentTime = ref(formatCurrentTime())
let clockTimer: number | undefined

const pageMeta: Record<string, { title: string; subtitle: string; breadcrumb: string }> = {
  '/dashboard': { title: '监控总览', subtitle: '实时检测概览 · 今日事件 · 资源状态 · 识别类别分布', breadcrumb: '监控中心' },
  '/training-analysis': { title: '训练分析', subtitle: '解析 YOLO results.csv，查看训练曲线、最终指标和 AI 诊断建议。', breadcrumb: '训练分析' },
  '/detect': { title: '智能检测', subtitle: '选择单图、批量、视频或实时流检测工作流。', breadcrumb: '检测中心' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片并查看原图、检测图和目标列表。', breadcrumb: '检测 / 单图' },
  '/detect/batch': { title: '批量检测', subtitle: '多图队列逐张检测，支持暂停、继续、结束和进度反馈。', breadcrumb: '检测 / 批量' },
  '/detect/video': { title: '视频审核台', subtitle: '创建异步视频检测任务，查看帧流、进度和检测结果。', breadcrumb: '检测 / 视频' },
  '/detect/realtime': { title: '实时监控', subtitle: '连接摄像头、RTSP 或 HTTP(S) 流，实时返回标注画面。', breadcrumb: '检测 / 实时' },
  '/history': { title: '事件档案库', subtitle: '按来源、类别、用户与时间追溯检测记录和结构化框数据。', breadcrumb: '事件档案' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活 YOLO 模型并维护 GPU 与类别中文映射。', breadcrumb: '模型中心' },
  '/logs': { title: '审计日志', subtitle: '查看登录、检测、模型切换与任务执行日志，按级别和来源筛选。', breadcrumb: '审计日志' },
  '/admin/users': { title: '用户管理', subtitle: '维护用户、角色、账号状态、最后登录时间和密码重置。', breadcrumb: '用户管理' },
  '/maintenance': { title: '系统维护', subtitle: '检查 GPU、模型、数据库、文件系统状态，并执行受控清理和初始化恢复。', breadcrumb: '系统维护' },
  '/assistant': { title: '运维助手', subtitle: '接入 DeepSeek 或 OpenAI 兼容模型进行独立问答，辅助排查与诊断。', breadcrumb: 'AI 助手' },
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
