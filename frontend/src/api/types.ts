export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface DetectionResult {
  class: string
  confidence: number
  bbox: [number, number, number, number]
  frame_id?: number | null
}

export interface AIAnalysis {
  summary: string
  class_distribution: Array<{ class: string; count: number; avg_confidence: number; ratio: number }>
  anomaly_tips: string[]
}

export interface User {
  id: number
  username: string
  is_active: boolean
  is_superuser: boolean
  roles: Role[]
}

export interface Role {
  id: number
  name: string
  description: string
  permissions: Permission[]
}

export interface Permission {
  id: number
  code: string
  name: string
  description: string
}

export interface ModelInfo {
  id: number
  name: string
  path: string
  version: string
  class_names_json: string
  is_active: boolean
  device: string
  created_at: string
  updated_at: string
}

export interface TaskInfo {
  id: number
  type: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress: number
  record_id: number | null
  result_json: string
  retry_count: number
  max_retries: number
  error_message: string
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}
