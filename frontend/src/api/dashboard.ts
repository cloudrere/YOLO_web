import { request, unwrap } from './request'

export interface DashboardMetrics {
  total_detections: number
  image_count: number
  video_count: number
  active_users: number
  daily_trend_7d: Array<{ date: string; count: number }>
  top_detected_classes: Array<{ class: string; count: number }>
}

export function getDashboardMetrics() {
  return unwrap<DashboardMetrics>(request.get('/dashboard/metrics'))
}
