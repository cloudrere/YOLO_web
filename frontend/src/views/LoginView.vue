<template>
  <div class="login-page">
    <section class="login-hero zh-hero">
      <span class="eyebrow">通用目标检测平台模板</span>
      <h1>YOLO 视觉检测中台</h1>
      <p>面向图片、批量图片与视频的可复用检测系统。模型驱动、权限完备、结果可追溯，不绑定任何具体业务类别。</p>
      <div class="hero-stats">
        <div><strong>YOLOv8</strong><span>工程化封装</span></div>
        <div><strong>RBAC</strong><span>权限体系</span></div>
        <div><strong>Video</strong><span>异步任务</span></div>
      </div>
    </section>
    <el-card class="login-card glass-card">
      <span class="eyebrow dark">安全登录</span>
      <h2>进入检测工作台</h2>
      <p class="form-subtitle">使用管理员或已授权账号访问模型、检测、历史与日志模块。</p>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" size="large" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" size="large" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="full login-button" size="large" @click="submit">登录系统</el-button>
        <p class="hint">默认账号：admin / admin123456</p>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123456' })

async function submit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>
