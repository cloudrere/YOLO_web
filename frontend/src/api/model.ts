import { request, unwrap } from './request'
import type { ModelInfo } from './types'

export function listModels() {
  return unwrap<{ items: ModelInfo[] }>(request.get('/models'))
}

export function registerModel(payload: { name: string; path: string; version?: string; class_names?: string[] }) {
  return unwrap<ModelInfo>(request.post('/models', payload))
}

export function uploadModel(file: File, name?: string, version = '') {
  const form = new FormData()
  form.append('file', file)
  if (name) form.append('name', name)
  form.append('version', version)
  return unwrap<ModelInfo>(request.post('/models/upload', form))
}

export function activateModel(id: number) {
  return unwrap<ModelInfo>(request.post(`/models/${id}/activate`))
}

export function activeModel() {
  return unwrap<{ active_model: ModelInfo | null; engine_loaded: boolean; device: string; cuda_available: boolean; model_path: string }>(
    request.get('/models/active'),
  )
}
