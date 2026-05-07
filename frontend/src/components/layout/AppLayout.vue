<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Y</div>
        <div>
          <strong>YOLO Vision</strong>
          <span>Reusable Detection Platform</span>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="menu">
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/dashboard">Dashboard</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('detect:run')" index="/detect">Detection</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('history:read')" index="/history">History</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('model:read')" index="/models">Models</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('log:read')" index="/logs">Logs</el-menu-item>
        <el-menu-item v-if="auth.hasPermission('admin:user')" index="/admin/users">Users</el-menu-item>
      </el-menu>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <h1>{{ title }}</h1>
          <p>Generic, model-driven object detection system.</p>
        </div>
        <div class="user-box">
          <span>{{ auth.user?.username }}</span>
          <el-button @click="logout">Logout</el-button>
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
const title = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  return String(parts[parts.length - 1] || 'dashboard').replace('-', ' ')
})
function logout() {
  auth.logout()
  router.push('/login')
}
</script>
