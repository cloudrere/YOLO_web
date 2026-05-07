<template>
  <div class="login-page">
    <section class="login-hero">
      <span class="eyebrow">Industrial CV Template</span>
      <h1>Reusable YOLO Visual Detection Platform</h1>
      <p>Model-driven object detection for images, batches, and videos without business-specific assumptions.</p>
    </section>
    <el-card class="login-card">
      <h2>Sign in</h2>
      <el-form :model="form" @keyup.enter="submit">
        <el-form-item label="Username">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="full" @click="submit">Login</el-button>
        <p class="hint">Default: admin / admin123456</p>
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
