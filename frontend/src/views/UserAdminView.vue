<template>
  <AppLayout>
    <section class="grid two">
      <el-card shadow="never">
        <template #header>Create User</template>
        <el-form :model="form" label-width="110px">
          <el-form-item label="Username"><el-input v-model="form.username" /></el-form-item>
          <el-form-item label="Password"><el-input v-model="form.password" type="password" /></el-form-item>
          <el-form-item label="Active"><el-switch v-model="form.is_active" /></el-form-item>
          <el-form-item label="Superuser"><el-switch v-model="form.is_superuser" /></el-form-item>
          <el-form-item label="Roles">
            <el-select v-model="form.role_ids" multiple style="width: 100%">
              <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
            </el-select>
          </el-form-item>
          <el-button type="primary" @click="create">Create</el-button>
        </el-form>
      </el-card>
      <el-card shadow="never">
        <template #header>Permissions</template>
        <el-tag v-for="permission in permissions" :key="permission.id" class="tag">{{ permission.code }}</el-tag>
      </el-card>
    </section>
    <el-card shadow="never">
      <template #header><div class="toolbar"><span>Users</span><el-button @click="load">Refresh</el-button></div></template>
      <el-table :data="users">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="Username" />
        <el-table-column prop="is_active" label="Active" width="100" />
        <el-table-column prop="is_superuser" label="Super" width="100" />
        <el-table-column label="Roles">
          <template #default="{ row }">{{ row.roles.map((role: any) => role.name).join(', ') }}</template>
        </el-table-column>
        <el-table-column label="Actions" width="120">
          <template #default="{ row }"><el-button type="danger" size="small" @click="remove(row.id)">Delete</el-button></template>
        </el-table-column>
      </el-table>
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
