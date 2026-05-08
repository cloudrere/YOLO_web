import { request, unwrap } from './request'
import type { AIAnalysis, DetectionResult, TaskInfo } from './types'

export interface ImageDetectResult {
  record_id: number
  results: DetectionResult[]
  analysis: AIAnalysis
  duration_ms: number
  result_url: string
}

export interface BatchDetectResult {
  items: Array<{
    file_name: string
    status: string
    record_id: number | null
    results: DetectionResult[]
    analysis?: AIAnalysis
    error: string
    result_url: string
  }>
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

export function withToken(path: string) {
  const token = encodeURIComponent(localStorage.getItem('access_token') || '')
  const separator = path.includes('?') ? '&' : '?'
  return `${path}${separator}token=${token}`
}

export function apiMediaUrl(path: string) {
  const base = import.meta.env.VITE_API_BASE || '/api'
  const normalizedPath = path.startsWith('/api') ? path.slice(4) : path
  return withToken(`${base}${normalizedPath}`)
}

export function artifactUrl(recordId: number) {
  return apiMediaUrl(`/detect/artifacts/${recordId}`)
}

export function videoStreamUrl(taskId: number) {
  return apiMediaUrl(`/detect/video/stream/${taskId}`)
}

export function realtimeStreamUrl(source: string) {
  const encodedSource = encodeURIComponent(source || '0')
  return apiMediaUrl(`/detect/realtime/stream?source=${encodedSource}`)
}
