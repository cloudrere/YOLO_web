import { request, unwrap } from './request'
import type { Permission, Role, User } from './types'

export function listUsers() {
  return unwrap<{ items: User[]; total: number }>(request.get('/admin/users'))
}

export function createUser(payload: { username: string; password: string; is_active: boolean; is_superuser: boolean; role_ids: number[] }) {
  return unwrap<User>(request.post('/admin/users', payload))
}

export function updateUser(id: number, payload: { password?: string; is_active?: boolean; is_superuser?: boolean; role_ids?: number[] }) {
  return unwrap<User>(request.put(`/admin/users/${id}`, payload))
}

export function deleteUser(id: number) {
  return unwrap<{ deleted: boolean }>(request.delete(`/admin/users/${id}`))
}

export function listRoles() {
  return unwrap<{ items: Role[]; total: number }>(request.get('/admin/roles'))
}

export function listPermissions() {
  return unwrap<{ items: Permission[]; total: number }>(request.get('/admin/permissions'))
}
