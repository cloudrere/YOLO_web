<template>
  <AppLayout>
    <section class="grid two">
      <el-card shadow="never" class="panel-card">
        <template #header>创建用户</template>
        <el-form :model="form" label-width="110px">
          <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="form.password" type="password" /></el-form-item>
          <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
          <el-form-item label="超级管理员"><el-switch v-model="form.is_superuser" /></el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role_ids" multiple style="width: 100%">
              <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
            </el-select>
          </el-form-item>
          <el-button type="primary" @click="create">创建用户</el-button>
        </el-form>
      </el-card>
      <el-card shadow="never" class="panel-card">
        <template #header>权限码</template>
        <el-tag v-for="permission in permissions" :key="permission.id" class="tag">{{ permission.code }}</el-tag>
      </el-card>
    </section>
    <el-card shadow="never" class="panel-card">
      <template #header><div class="toolbar"><span>用户列表</span><el-button @click="load">刷新</el-button></div></template>
      <div class="table-scroll user-table-shell">
        <el-table :data="users">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="is_active" label="启用" width="100" />
          <el-table-column prop="is_superuser" label="超管" width="100" />
          <el-table-column label="角色">
            <template #default="{ row }">{{ row.roles.map((role: any) => role.name).join(', ') }}</template>
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
import AppLayout from '@/components/layout/AppLayout.vue'
import { createUser, deleteUser, listPermissions, listRoles, listUsers } from '@/api/admin'
import type { Permission, Role, User } from '@/api/types'

const users = ref<User[]>([])
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const form = reactive({ username: '', password: '', is_active: true, is_superuser: false, role_ids: [] as number[] })
async function load() {
  users.value = (await listUsers()).items
  roles.value = (await listRoles()).items
  permissions.value = (await listPermissions()).items
}
async function create() {
  await createUser(form)
  Object.assign(form, { username: '', password: '', is_active: true, is_superuser: false, role_ids: [] })
  await load()
}
async function remove(id: number) {
  await deleteUser(id)
  await load()
}
onMounted(load)
</script>
