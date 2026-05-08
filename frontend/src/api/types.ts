export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface DetectionResult {
  class: string
  class_zh?: string
  confidence: number
  bbox: [number, number, number, number]
  frame_id?: number | null
}

export interface AIAnalysis {
  summary: string
  class_distribution: Array<{ class: string; class_zh?: string; count: number; avg_confidence: number; ratio: number }>
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
  display_name: string
  path: string
  version: string
  class_names_json: string
  class_mapping_json: string
  is_active: boolean
  is_deleted: boolean
  device: string
  created_at: string
  updated_at: string
}

export interface ModelDeviceInfo {
  value: string
  label: string
  type: 'auto' | 'cpu' | 'cuda' | string
  available: boolean
  total_memory?: number | null
}

export interface ModelEngineState {
  active_model: ModelInfo | null
  engine_loaded: boolean
  device: string
  requested_device: string
  available_devices: ModelDeviceInfo[]
  cuda_available: boolean
  cuda_name: string
  model_path: string
  class_names?: string[]
  warmup_status: string
  warmup_error: string
}

export interface TaskInfo {
  id: number
  type: string
  status: 'pending' | 'running' | 'paused' | 'cancelled' | 'done' | 'failed'
  progress: number
  user_id?: number | null
  record_id: number | null
  result_json: string
  retry_count: number
  max_retries: number
  error_message: string
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}
