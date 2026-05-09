<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div>
          <strong>YOLO 检测工作台</strong>
          <span>智能视觉分析</span>
        </div>
      </div>

      <el-menu :default-active="activeMenuPath" router class="menu">
        <el-menu-item index="/dashboard">工作台首页</el-menu-item>
        <el-menu-item index="/detect">检测模式</el-menu-item>
        <el-menu-item index="/history">检测结果</el-menu-item>
        <el-menu-item index="/models">模型中心</el-menu-item>
        <el-menu-item index="/training-analysis">训练实验室</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">AI 助手</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">系统日志</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">用户管理</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/maintenance">运行环境</el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <span>运行模式</span>
        <strong>本地推理引擎</strong>
        <small>{{ currentTime }}</small>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-page">
          <h1>{{ meta.title }}</h1>
          <p>{{ meta.subtitle }}</p>
        </div>
        <div class="user-box">
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
const currentTime = ref(formatTime())
let timer: number | undefined

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: '检测工作台', subtitle: '当前模型状态、近期检测统计与系统资源概览。' },
  '/training-analysis': { title: '训练实验室', subtitle: '解析 YOLO results.csv，分析训练曲线、最终指标与 AI 诊断。' },
  '/detect': { title: '选择检测模式', subtitle: '单图、批量图片、视频文件或实时摄像头流 — 四种模式独立运行。' },
  '/detect/image': { title: '单图检测', subtitle: '上传图片，配置参数，查看检测框与目标分类。' },
  '/detect/batch': { title: '批量图片检测', subtitle: '多图队列顺序推理，监控进度、暂停或终止任务。' },
  '/detect/video': { title: '视频文件检测', subtitle: '提交异步任务，查看帧流与检测进度。' },
  '/detect/realtime': { title: '实时流检测', subtitle: '接入摄像头、RTSP 或 HTTP 流，实时返回标注画面。' },
  '/history': { title: '检测结果中心', subtitle: '按来源、类别、用户追溯检测记录，查看完整检测证据。' },
  '/models': { title: '模型中心', subtitle: '管理 YOLO 模型：上传、登记、激活、设备切换与类别映射。' },
  '/logs': { title: '系统日志', subtitle: '查看登录、检测、模型切换与任务执行日志。' },
  '/admin/users': { title: '用户管理', subtitle: '创建和管理用户账号与角色权限。' },
  '/maintenance': { title: '运行环境体检', subtitle: '检查 GPU、模型、数据库、文件系统状态与清理操作。' },
  '/assistant': { title: 'AI 检测助手', subtitle: '内置专家：解答检测结果、模型训练、设备问题与日志排查。' },
}

const meta = computed(() => pageMeta[route.path] || { title: '检测工作台', subtitle: '' })
const activeMenuPath = computed(() => {
  if (route.path.startsWith('/detect')) return '/detect'
  return route.path
})

function formatTime() {
  return new Date().toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

onMounted(() => { timer = window.setInterval(() => { currentTime.value = formatTime() }, 1000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

function logout() { auth.logout(); router.push('/login') }
</script>
