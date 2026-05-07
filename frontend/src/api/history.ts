import { request, unwrap } from './request'
import type { AIAnalysis, DetectionResult } from './types'

export interface HistoryItem {
  id: number
  user_id: number | null
  model_id: number | null
  source_type: string
  file_name: string
  file_path: string
  status: string
  duration_ms: number
  created_at: string
  result_count: number
}

export interface HistoryDetail extends HistoryItem {
  result_path: string
  results: DetectionResult[]
  analysis: AIAnalysis
}

export function listHistory(params: Record<string, unknown>) {
  return unwrap<{ items: HistoryItem[]; total: number; page: number; page_size: number }>(request.get('/history', { params }))
}

export function getHistory(id: number) {
  return unwrap<HistoryDetail>(request.get(`/history/${id}`))
}

export function deleteHistory(id: number) {
  return unwrap<{ deleted: number }>(request.delete(`/history/${id}`))
}
