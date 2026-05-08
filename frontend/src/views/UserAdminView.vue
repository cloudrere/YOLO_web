<template>
  <AppLayout>
    <section class="grid">
      <el-card shadow="never" class="panel-card">
        <template #header>创建用户</template>
        <el-form :model="form" label-width="110px">
          <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="form.password" type="password" /></el-form-item>
          <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
          <el-form-item label="超级管理员"><el-switch v-model="form.is_superuser" /></el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role_ids" multiple style="width: 100%">
              <el-option v-for="role in roles" :key="role.id" :label="roleLabel(role)" :value="role.id" />
            </el-select>
          </el-form-item>
          <el-button type="primary" @click="create">创建用户</el-button>
        </el-form>
      </el-card>
    </section>
    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="toolbar"><span>用户列表</span><el-button @click="load">刷新</el-button></div>
      </template>
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="用户查询">
          <el-input v-model="keyword" clearable placeholder="输入用户名关键词" @keyup.enter="load" />
        </el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form>
      <div class="table-scroll user-table-shell">
        <el-table :data="users">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column label="启用" width="100">
            <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="超管" width="100">
            <template #default="{ row }"><el-tag :type="row.is_superuser ? 'danger' : 'info'">{{ row.is_superuser ? '是' : '否' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="角色">
            <template #default="{ row }">{{ row.roles.map((role: Role) => roleLabel(role)).join(', ') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }"><el-button type="danger" size="small" @click="remove(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import { createUser, deleteUser, listRoles, listUsers } from '@/api/admin'
import type { Role, User } from '@/api/types'

const users = ref<User[]>([])
const roles = ref<Role[]>([])
const keyword = ref('')
const form = reactive({ username: '', password: '', is_active: true, is_superuser: false, role_ids: [] as number[] })
const roleNameMap: Record<string, string> = {
  admin: '管理员',
  operator: '操作员',
  user: '普通用户',
  viewer: '只读用户',
}
function roleLabel(role: Role) {
  return roleNameMap[role.name] || role.description || role.name
}
async function load() {
  users.value = (await listUsers(keyword.value)).items
  roles.value = (await listRoles()).items
}
async function create() {
  const username = form.username.trim()
  const password = form.password.trim()
  if (!username || !password) {
    ElMessage.warning('用户名和密码不能为空')
    return
  }
  await createUser({ ...form, username, password })
  Object.assign(form, { username: '', password: '', is_active: true, is_superuser: false, role_ids: [] })
  ElMessage.success('用户已创建')
  await load()
}
async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这个用户吗？删除后该账号将无法继续登录。', '删除确认', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteUser(id)
  ElMessage.success('用户已删除')
  await load()
}
onMounted(load)
</script>
