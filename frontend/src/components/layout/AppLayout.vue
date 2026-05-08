<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">检</div>
        <div>
          <strong>YOLO 视觉中台</strong>
          <span>智能检测工作台</span>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">数据总览</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">智能检测</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">检测历史</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">模型管理</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">日志中心</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">用户权限</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('assistant:use')" index="/assistant">AI 助手</el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <span>运行模式</span>
        <strong>本地推理</strong>
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const pageMeta: Record<string, { title: string; subtitle: string; breadcrumb: string }> = {
  '/dashboard': { title: '数据总览', subtitle: '集中展示检测量、用户统计、系统资源与类别分布趋势。', breadcrumb: '总览' },
  '/detect': { title: '智能检测', subtitle: '支持图片、视频文件与实时视频流检测，可调节参数并选择保存策略。', breadcrumb: '检测' },
  '/history': { title: '检测历史', subtitle: '按来源、中文类别、用户与时间追溯检测记录和结构化框数据。', breadcrumb: '历史' },
  '/models': { title: '模型管理', subtitle: '上传、登记、激活 YOLO 模型并维护 GPU 与类别中文映射。', breadcrumb: '模型' },
  '/logs': { title: '日志中心', subtitle: '查看登录、检测、模型切换与任务执行日志，中文显示关键字段。', breadcrumb: '日志' },
  '/admin/users': { title: '用户权限', subtitle: '维护用户、角色与权限，支持关键词快速查询用户。', breadcrumb: '权限' },
  '/assistant': { title: 'AI 助手', subtitle: '接入 DeepSeek 或 OpenAI 兼容模型进行独立问答，不影响检测主流程。', breadcrumb: '助手' },
}
const meta = computed(() => pageMeta[route.path] || pageMeta['/dashboard'])
const title = computed(() => meta.value.title)
const subtitle = computed(() => meta.value.subtitle)
const breadcrumb = computed(() => meta.value.breadcrumb)
function logout() {
  auth.logout()
  router.push('/login')
}
</script>
