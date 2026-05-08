import { request, unwrap } from './request'

export interface LogItem {
  id: number
  type: string
  type_zh: string
  level: string
  level_zh: string
  module: string
  module_zh: string
  message: string
  user_id: number | null
  request_id: string
  created_at: string
}

export function listLogs(params: Record<string, unknown>) {
  return unwrap<{ items: LogItem[]; total: number; page: number; page_size: number }>(request.get('/logs', { params }))
}

export function deleteLog(id: number) {
  return unwrap<{ deleted: number }>(request.delete(`/logs/${id}`))
}

export function deleteLogsBatch(ids: number[]) {
  return unwrap<{ deleted: number }>(request.delete('/logs/batch/delete', { data: { ids } }))
}

export function deleteLogsByDate(start_date: string, end_date: string) {
  return unwrap<{ deleted: number }>(request.delete('/logs/by-date', { data: { start_date, end_date } }))
}
