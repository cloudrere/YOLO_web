import { request, unwrap } from './request'
import type { AIAnalysis, DetectionResult, TaskInfo } from './types'

export interface ImageDetectResult {
  record_id: number
  results: DetectionResult[]
  analysis: AIAnalysis
  duration_ms: number
}

export interface BatchDetectResult {
  items: Array<{ file_name: string; status: string; record_id: number | null; results: DetectionResult[]; analysis?: AIAnalysis; error: string }>
}

export function detectImage(file: File) {
  const form = new FormData()
  form.append('file', file)
  return unwrap<ImageDetectResult>(request.post('/detect/image', form))
}

export function detectBatch(files: File[]) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  return unwrap<BatchDetectResult>(request.post('/detect/batch', form))
}

export function detectVideo(file: File) {
  const form = new FormData()
  form.append('file', file)
  return unwrap<{ task_id: number; record_id: number; status: string }>(request.post('/detect/video', form))
}

export function getTask(taskId: number) {
  return unwrap<TaskInfo>(request.get(`/detect/tasks/${taskId}`))
}

export function videoStreamUrl(taskId: number) {
  const base = import.meta.env.VITE_API_BASE || '/api'
  const token = encodeURIComponent(localStorage.getItem('access_token') || '')
  return `${base}/detect/video/stream/${taskId}?token=${token}`
}
