import { request, unwrap } from './request'
import type { DetectionResult, TaskInfo } from './types'

export interface DetectParameters {
  confidence?: number
  iou?: number
  save_history?: boolean
}

export interface ImageDetectResult {
  record_id: number | null
  results: DetectionResult[]
  duration_ms: number
  original_url: string
  result_url: string
  model_name: string
  device: string
  parameters: DetectParameters
}

export interface BatchDetectResult {
  items: Array<{
    file_name: string
    status: string
    record_id: number | null
    results: DetectionResult[]
    error: string
    original_url: string
    result_url: string
    duration_ms: number
  }>
  parameters: DetectParameters
}

function appendParameters(form: FormData, params?: DetectParameters) {
  if (!params) return
  if (params.confidence !== undefined) form.append('confidence', String(params.confidence))
  if (params.iou !== undefined) form.append('iou', String(params.iou))
  if (params.save_history !== undefined) form.append('save_history', String(params.save_history))
}

export function detectImage(file: File, params?: DetectParameters) {
  const form = new FormData()
  form.append('file', file)
  appendParameters(form, params)
  return unwrap<ImageDetectResult>(request.post('/detect/image', form))
}

export function detectBatch(files: File[], params?: DetectParameters) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  appendParameters(form, params)
  return unwrap<BatchDetectResult>(request.post('/detect/batch', form))
}

export function detectVideo(file: File, params?: DetectParameters) {
  const form = new FormData()
  form.append('file', file)
  appendParameters(form, params)
  return unwrap<{ task_id: number; record_id: number; status: string; original_url: string; parameters: DetectParameters }>(request.post('/detect/video', form))
}

export function getTask(taskId: number) {
  return unwrap<TaskInfo>(request.get(`/detect/tasks/${taskId}`))
}

export function controlTask(taskId: number, action: 'pause' | 'resume' | 'cancel' | 'end') {
  return unwrap<TaskInfo>(request.post(`/detect/tasks/${taskId}/${action}`))
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

export function artifactUrl(recordId: number, kind = 'result') {
  return apiMediaUrl(`/detect/artifacts/${recordId}?kind=${kind}`)
}

export function videoStreamUrl(taskId: number) {
  return apiMediaUrl(`/detect/video/stream/${taskId}`)
}

export function realtimeStreamUrl(source: string, params?: DetectParameters) {
  const query = new URLSearchParams({ source: source || '0' })
  if (params?.confidence !== undefined) query.set('confidence', String(params.confidence))
  if (params?.iou !== undefined) query.set('iou', String(params.iou))
  return apiMediaUrl(`/detect/realtime/stream?${query.toString()}`)
}
