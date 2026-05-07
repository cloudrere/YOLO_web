import { request, unwrap } from './request'

export interface LogItem {
  id: number
  type: string
  level: string
  module: string
  message: string
  user_id: number | null
  request_id: string
  created_at: string
}

export function listLogs(params: Record<string, unknown>) {
  return unwrap<{ items: LogItem[]; total: number; page: number; page_size: number }>(request.get('/logs', { params }))
}
