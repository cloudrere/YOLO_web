<template>
  <div class="ws-login-page">
    <div class="ws-login-card">
      <h2>{{ modeMeta.title }}</h2>
      <p class="login-sub">{{ modeMeta.subtitle }}</p>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item :label="mode === 'reset' ? '新密码' : '密码'">
          <el-input v-model="form.password" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" show-password :placeholder="mode === 'reset' ? '请输入新密码' : '请输入密码'" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="full" @click="submit">{{ modeMeta.button }}</el-button>
        <div class="ws-login-links">
          <el-button link type="primary" @click="setMode('login')">登录</el-button>
          <el-button link type="primary" @click="setMode('register')">注册账号</el-button>
          <el-button link type="primary" @click="setMode('reset')">忘记密码</el-button>
        </div>
        <p class="ws-login-hint">默认账号：admin / admin123456；注册账号默认获得操作员权限。</p>
      </el-form>
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
  login: { title: 'YOLO 视觉实验工作站', subtitle: '使用管理员或已授权账号访问检测工作台。', button: '登录系统' },
  register: { title: '注册账号', subtitle: '创建操作员账号，默认获得操作员权限。', button: '注册账号' },
  reset: { title: '重置密码', subtitle: '输入用户名和新密码即可完成重置。', button: '重置密码' },
}[mode.value]))

function setMode(nextMode: 'login' | 'register' | 'reset') {
  mode.value = nextMode
  if (nextMode !== 'login' && form.username === 'admin') Object.assign(form, { username: '', password: '' })
}
async function submit() {
  if (!form.username || !form.password) { ElMessage.warning('请输入用户名和密码'); return }
  loading.value = true
  try {
    if (mode.value === 'login') { await auth.login(form.username, form.password); router.push('/dashboard'); return }
    if (mode.value === 'register') { await register(form.username, form.password); ElMessage.success('注册成功，请登录') }
    else { await resetPassword(form.username, form.password); ElMessage.success('密码已重置，请登录') }
    mode.value = 'login'
  } finally { loading.value = false }
}
</script>
