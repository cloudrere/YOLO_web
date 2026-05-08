import { request, unwrap } from './request'
import type { AIAnalysis, DetectionResult } from './types'

export interface HistoryClassSummary {
  class: string
  class_zh: string
  count: number
  avg_confidence: number
}

export interface HistoryItem {
  id: number
  user_id: number | null
  username: string
  model_id: number | null
  model_name: string
  source_type: string
  file_name: string
  file_path: string
  original_path: string
  result_path: string
  original_url: string
  result_url: string
  video_stream_url?: string
  status: string
  duration_ms: number
  created_at: string
  created_at_text: string
  result_count: number
  classes: HistoryClassSummary[]
  confidence_threshold: number
  iou_threshold: number
  save_history: boolean
  device: string
  parameters: Record<string, unknown>
}

export interface HistoryDetail extends HistoryItem {
  results: DetectionResult[]
  analysis: AIAnalysis | null
}

export function listHistory(params: Record<string, unknown>) {
  return unwrap<{ items: HistoryItem[]; total: number; page: number; page_size: number }>(request.get('/history', { params }))
}

export function getHistory(id: number) {
  return unwrap<HistoryDetail>(request.get(`/history/${id}`))
}

export function exportHistory(params: Record<string, unknown>) {
  return request.get('/history/export', { params, responseType: 'blob' })
}

export function deleteHistory(id: number) {
  return unwrap<{ deleted: number }>(request.delete(`/history/${id}`))
}

export function deleteHistoryBatch(ids: number[]) {
  return unwrap<{ deleted: number }>(request.delete('/history/batch/delete', { data: { ids } }))
}
