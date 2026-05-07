import { request, unwrap } from './request'
import type { User } from './types'

export interface LoginResult {
  access_token: string
  token_type: string
  user: User
  permissions: string[]
}

export function login(username: string, password: string) {
  return unwrap<LoginResult>(request.post('/auth/login', { username, password }))
}

export function me() {
  return unwrap<{ user: User; permissions: string[] }>(request.get('/auth/me'))
}
