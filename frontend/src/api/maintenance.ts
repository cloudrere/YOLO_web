import { request, unwrap } from './request'

export interface MaintenanceStatus {
  gpu: {
    cuda_available: boolean
    torch_available: boolean
    torch_version: string
    torch_cuda_version: string
    device_count: number
    gpu_name: string
    memory_total: number
    memory_reserved: number
    memory_allocated: number
    diagnostics: Array<{ name: string; status: string; message: string }>
  }
  model: {
    active_model_id: number | null
    active_model_name: string
    active_model_path: string
    active_model_exists: boolean
    active_model_size: number
    total_models: number
  }
  database: {
    connected: boolean
    tables_ok: boolean
    missing_tables: string[]
    table_count: number
    error?: string
  }
  filesystem: {
    paths: Record<string, { path: string; exists: boolean; is_dir: boolean }>
    disk: { total: number; used: number; free: number }
  }
}

export function getMaintenanceStatus() {
  return unwrap<MaintenanceStatus>(request.get('/maintenance/status'))
}

export function clearMaintenanceHistory() {
  return unwrap<{ deleted: number }>(request.delete('/maintenance/history'))
}

export function clearMaintenanceLogs() {
  return unwrap<{ deleted: number }>(request.delete('/maintenance/logs'))
}

export function clearMaintenanceModels() {
  return unwrap<{ deleted: number }>(request.delete('/maintenance/models'))
}

export function restoreInitialState() {
  return unwrap<{ restored: boolean }>(request.post('/maintenance/restore-initial'))
}
