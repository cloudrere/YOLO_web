<template>
  <div class="bi-login-page">
    <div class="bi-login-container">
      <div class="bi-login-header">
        <h1>YOLO 视觉检测系统</h1>
        <p>数据分析平台</p>
      </div>
      <el-card class="bi-login-card" shadow="never">
        <span class="eyebrow">{{ modeMeta.eyebrow }}</span>
        <h2>{{ modeMeta.title }}</h2>
        <p class="bi-login-desc">{{ modeMeta.subtitle }}</p>
        <el-form :model="form" label-position="top" @keyup.enter="submit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" autocomplete="username" size="large" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item :label="mode === 'reset' ? '新密码' : '密码'">
            <el-input
              v-model="form.password"
              type="password"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              size="large"
              show-password
              :placeholder="mode === 'reset' ? '请输入新密码' : '请输入密码'"
            />
          </el-form-item>
          <el-button type="primary" :loading="loading" class="full" size="large" @click="submit">{{ modeMeta.button }}</el-button>
          <div class="bi-login-links">
            <el-button link type="primary" @click="setMode('login')">登录</el-button>
            <el-button link type="primary" @click="setMode('register')">注册账号</el-button>
            <el-button link type="primary" @click="setMode('reset')">忘记密码</el-button>
          </div>
          <p class="bi-hint">默认账号：admin / admin123456；注册账号默认获得操作员权限。</p>
        </el-form>
      </el-card>
    </div>
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
