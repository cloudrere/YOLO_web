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
  torch_version: string
  torch_cuda_version: string
  cuda_available: boolean
  cuda_device_count: number
  cuda_error: string
  diagnostics: {
    requested_device: string
    resolved_device: string
    torch_version: string
    torch_cuda_version: string
    cuda_available: boolean
    cuda_device_count: number
    warmup_error: string
    checks: Array<{ name: string; status: 'ok' | 'info' | 'warning' | 'error' | string; message: string }>
  }
  engine: Record<string, unknown>
}

export interface DashboardMetrics {
  total_detections: number
  image_count: number
  video_count: number
  active_users: number
  daily_trend_7d: Array<{ date: string; count: number }>
  user_detection_trend_7d: Array<{ date: string; users: Record<string, number> }>
  class_distribution: Array<{ class: string; class_zh?: string; count: number; avg_confidence: number }>
  model_call_ranking: Array<{ model: string; count: number }>
  ai_call_trend_7d: Array<{ date: string; count: number }>
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
