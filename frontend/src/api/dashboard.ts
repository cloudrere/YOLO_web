import { request, unwrap } from './request'

export interface SystemStatus {
  cpu_percent: number | null
  memory: { total: number; available: number; used: number; percent: number } | null
  temperature: number | null
  gpu_devices: Array<{
    index: number
    name: string
    total_memory: number
    allocated_memory: number
    reserved_memory: number
    temperature: number | null
  }>
  engine: Record<string, unknown>
}

export interface DashboardMetrics {
  total_detections: number
  image_count: number
  video_count: number
  active_users: number
  daily_trend_7d: Array<{ date: string; count: number }>
  top_detected_classes: Array<{ class: string; class_zh?: string; count: number }>
  admin?: {
    total_users: number
    total_models: number
    abnormal_logs: number
    ai_call_count: number
    user_detection_stats: Array<{ user_id: number; username: string; count: number }>
    system_status: SystemStatus
  }
}

export function getDashboardMetrics() {
  return unwrap<DashboardMetrics>(request.get('/dashboard/metrics'))
}
