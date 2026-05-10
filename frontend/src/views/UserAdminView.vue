<template>
  <AppLayout>
    <el-card shadow="never" class="panel-card create-user-card">
      <template #header>
        <div class="toolbar"><span>创建用户</span></div>
      </template>
      <el-form :model="form" :inline="true" class="create-user-form">
        <el-form-item label="用户名"><el-input v-model="form.username" placeholder="输入用户名" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" placeholder="输入密码" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple placeholder="选择角色" style="width: 200px">
            <el-option v-for="role in roles" :key="role.id" :label="roleLabel(role)" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
        <el-form-item label="超管"><el-switch v-model="form.is_superuser" /></el-form-item>
        <el-form-item>
          <el-button type="primary" @click="create">创建用户</el-button>
        </el-form-item>
      </el-form>
    </el-card>
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
        <el-table :data="users" row-key="id">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column label="启用" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                <StatusPulse :status="row.is_active ? 'success' : 'idle'" size="sm" />
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="超管" width="100">
            <template #default="{ row }"><el-tag :type="row.is_superuser ? 'danger' : 'info'">{{ row.is_superuser ? '是' : '否' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="角色" min-width="160">
            <template #default="{ row }">{{ row.roles.map((role: Role) => roleLabel(role)).join(', ') }}</template>
          </el-table-column>
          <el-table-column label="创建时间" width="190">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="最后登录" width="190">
            <template #default="{ row }">{{ formatTime(row.last_login_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="260">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleStatus(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
                <el-button size="small" @click="openResetPassword(row)">重置密码</el-button>
                <el-button type="danger" size="small" @click="remove(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    <el-dialog v-model="resetDialog" title="重置密码" width="420px">
      <el-form label-position="top">
        <el-form-item label="用户名"><el-input :model-value="selectedUser?.username || ''" disabled /></el-form-item>
        <el-form-item label="新密码" required><el-input v-model="resetPassword" type="password" show-password placeholder="请输入新密码" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialog = false">取消</el-button>
        <el-button type="primary" @click="saveResetPassword">保存</el-button>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppLayout from '@/components/layout/AppLayout.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'
import { createUser, deleteUser, listRoles, listUsers, updateUser } from '@/api/admin'
import type { Role, User } from '@/api/types'

const users = ref<User[]>([])
const roles = ref<Role[]>([])
const keyword = ref('')
const resetDialog = ref(false)
const resetPassword = ref('')
const selectedUser = ref<User | null>(null)
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
function formatTime(value?: string | null) {
  if (!value) return '从未登录'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
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
async function toggleStatus(row: User) {
  const next = !row.is_active
  try {
    await ElMessageBox.confirm(`确认${next ? '启用' : '停用'}用户 ${row.username} 吗？`, '状态确认', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' })
  } catch {
    return
  }
  await updateUser(row.id, { is_active: next })
  ElMessage.success(`用户已${next ? '启用' : '停用'}`)
  await load()
}
function openResetPassword(row: User) {
  selectedUser.value = row
  resetPassword.value = ''
  resetDialog.value = true
}
async function saveResetPassword() {
  const password = resetPassword.value.trim()
  if (!selectedUser.value || !password) {
    ElMessage.warning('新密码不能为空')
    return
  }
  await updateUser(selectedUser.value.id, { password })
  resetDialog.value = false
  ElMessage.success('密码已重置')
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

<style scoped>
.create-user-card {
  margin-bottom: var(--gap);
}

.create-user-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 4px 12px;
}

.create-user-form .el-form-item {
  margin-bottom: 0;
}

.el-table :deep(.el-tag) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>