<template>
  <div class="login-page">
    <section class="login-hero">
      <div class="hero-grid-bg"></div>
      <div class="hero-scan-line"></div>
      <div class="hero-detect-boxes">
        <div class="detect-anim-box box-1"></div>
        <div class="detect-anim-box box-2"></div>
        <div class="detect-anim-box box-3"></div>
      </div>
      <div class="hero-content">
        <div class="hero-brand">
          <div class="hero-logo">
            <svg viewBox="0 0 32 32" fill="none">
              <rect x="2" y="2" width="28" height="28" rx="4" stroke="currentColor" stroke-width="2.5"/>
              <circle cx="16" cy="16" r="5" stroke="currentColor" stroke-width="2"/>
              <path d="M16 6v4M16 22v4M6 16h4M22 16h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <span class="hero-eyebrow">目标检测工作台</span>
        </div>
        <h1 class="hero-title">YOLO<br/><span>视觉检测系统</span></h1>
        <p class="hero-desc">面向图片、视频与实时流的智能检测系统。模型驱动、权限完备、结果可追溯。</p>
        <div class="hero-stats">
          <div class="stat-item">
            <strong>YOLOv8</strong>
            <span>工程化封装</span>
          </div>
          <div class="stat-item">
            <strong>RBAC</strong>
            <span>权限体系</span>
          </div>
          <div class="stat-item">
            <strong>Video</strong>
            <span>异步任务</span>
          </div>
        </div>
      </div>
      <div class="hero-footer">
        <span>Powered by Ultralytics</span>
      </div>
    </section>

    <section class="login-form-section">
      <div class="login-card glass-card">
        <div class="card-header">
          <span class="card-eyebrow">{{ modeMeta.eyebrow }}</span>
          <h2 class="card-title">{{ modeMeta.title }}</h2>
          <p class="card-subtitle">{{ modeMeta.subtitle }}</p>
        </div>

        <el-form :model="form" label-position="top" class="login-form" @keyup.enter="submit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" autocomplete="username" size="large" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item :label="mode === 'reset' ? '新密码' : '密码'">
            <el-input
              v-model="form.password"
              type="password"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              size="large"
              show-password
              prefix-icon="Lock"
              :placeholder="mode === 'reset' ? '请输入新密码' : '请输入密码'"
            />
          </el-form-item>
          <el-button type="primary" :loading="loading" class="login-submit-btn" size="large" @click="submit">
            {{ modeMeta.button }}
          </el-button>
        </el-form>

        <div class="login-mode-switch">
          <button :class="['mode-btn', { active: mode === 'login' }]" @click="setMode('login')">登录</button>
          <button :class="['mode-btn', { active: mode === 'register' }]" @click="setMode('register')">注册账号</button>
          <button :class="['mode-btn', { active: mode === 'reset' }]" @click="setMode('reset')">忘记密码</button>
        </div>

        <p class="login-hint">默认账号：admin / admin123456</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register, resetPassword } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const mode = ref<'login' | 'register' | 'reset'>('login')
const form = reactive({ username: 'admin', password: 'admin123456' })

const modeMeta = computed(() => ({
  login: { eyebrow: '安全登录', title: '进入检测工作台', subtitle: '使用管理员或已授权账号访问模型、检测、历史与日志模块。', button: '登录系统' },
  register: { eyebrow: '注册账号', title: '创建操作员账号', subtitle: '输入用户名和密码即可注册普通账号，默认分配操作员权限。', button: '注册账号' },
  reset: { eyebrow: '忘记密码', title: '重置账号密码', subtitle: '输入用户名和新密码即可完成重置，不引入额外验证流程。', button: '重置密码' },
}[mode.value]))

function setMode(nextMode: 'login' | 'register' | 'reset') {
  mode.value = nextMode
  if (nextMode !== 'login' && form.username === 'admin') Object.assign(form, { username: '', password: '' })
}
async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.username, form.password)
      router.push('/dashboard')
      return
    }
    if (mode.value === 'register') {
      await register(form.username, form.password)
      ElMessage.success('注册成功，请登录')
    } else {
      await resetPassword(form.username, form.password)
      ElMessage.success('密码已重置，请登录')
    }
    mode.value = 'login'
  } finally {
    loading.value = false
  }
}
</script>
