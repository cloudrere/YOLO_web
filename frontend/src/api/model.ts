import { request, unwrap } from './request'
import type { ModelEngineState, ModelInfo } from './types'

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

export function activateModel(id: number, device?: string) {
  return unwrap<ModelInfo>(request.post(`/models/${id}/activate`, device ? { device } : undefined))
}

export function activeModel() {
  return unwrap<ModelEngineState>(request.get('/models/active'))
}

export function listModelDevices() {
  return unwrap<ModelEngineState>(request.get('/models/devices'))
}

export function switchModelDevice(device: string) {
  return unwrap<ModelEngineState>(request.post('/models/device', { device }))
}
