import { defineStore } from 'pinia'
import { login as loginApi, me } from '@/api/auth'
import type { User } from '@/api/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    user: null as User | null,
    permissions: [] as string[],
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    hasPermission: (state) => (code: string) => state.permissions.includes(code) || Boolean(state.user?.is_superuser),
  },
  actions: {
    async login(username: string, password: string) {
      const data = await loginApi(username, password)
      this.token = data.access_token
      this.user = data.user
      this.permissions = data.permissions
      localStorage.setItem('access_token', data.access_token)
    },
    async restore() {
      if (!this.token) return
      const data = await me()
      this.user = data.user
      this.permissions = data.permissions
    },
    logout() {
      this.token = ''
      this.user = null
      this.permissions = []
      localStorage.removeItem('access_token')
    },
  },
})
