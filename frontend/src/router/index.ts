import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import DetectionView from '@/views/DetectionView.vue'
import HistoryView from '@/views/HistoryView.vue'
import ModelManagementView from '@/views/ModelManagementView.vue'
import LogsView from '@/views/LogsView.vue'
import UserAdminView from '@/views/UserAdminView.vue'
import AssistantView from '@/views/AssistantView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: DashboardView, meta: { permission: 'history:read' } },
    { path: '/detect', component: DetectionView, meta: { permission: 'detect:run' } },
    { path: '/history', component: HistoryView, meta: { permission: 'history:read' } },
    { path: '/models', component: ModelManagementView, meta: { permission: 'model:read' } },
    { path: '/logs', component: LogsView, meta: { permission: 'log:read' } },
    { path: '/admin/users', component: UserAdminView, meta: { permission: 'admin:user' } },
    { path: '/assistant', component: AssistantView, meta: { permission: 'assistant:use' } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.isLoggedIn) return '/login'
  if (!auth.user) {
    try {
      await auth.restore()
    } catch {
      auth.logout()
      return '/login'
    }
  }
  const permission = to.meta.permission as string | undefined
  if (permission && !auth.hasPermission(permission)) return '/detect'
  return true
})

export default router
