import { request, unwrap } from './request'

export interface TrainingAnalysisFile {
  id: number | null
  name: string
  path: string
  rows: number
  best_epoch: number | null
  best_map50: number | null
  best_map5095: number | null
  file_size: number
  created_at: string
}

export interface TrainingAnalysisMetricItem {
  name: string
  value: number | string
}

export interface TrainingAnalysisSummary {
  name: string
  path: string
  epochs: number[]
  train_box_loss: number[]
  train_cls_loss: number[]
  train_dfl_loss: number[]
  precision: number[]
  recall: number[]
  map50: number[]
  map5095: number[]
  val_box_loss: number[]
  val_cls_loss: number[]
  val_dfl_loss: number[]
  lr_pg0: number[]
  lr_pg1: number[]
  lr_pg2: number[]
  radar: TrainingAnalysisMetricItem[]
  bar_metrics: TrainingAnalysisMetricItem[]
  best_epoch: number | null
  best_map50: number | null
  best_map5095: number | null
  final_metrics: Record<string, number>
  warnings: string[]
}

export interface TrainingAnalysisUploadResponse {
  file: TrainingAnalysisFile
  summary: TrainingAnalysisSummary
}

export interface TrainingAnalysisAiReport {
  answer: string
}

export function uploadTrainingResults(file: File) {
  const form = new FormData()
  form.append('file', file)
  return unwrap<TrainingAnalysisUploadResponse>(request.post('/training-analysis/upload', form))
}

export function listTrainingFiles() {
  return unwrap<{ items: TrainingAnalysisFile[] }>(request.get('/training-analysis/files'))
}

export function getTrainingSummary(name: string) {
  return unwrap<TrainingAnalysisSummary>(request.get('/training-analysis/summary', { params: { name } }))
}

export function getTrainingAiReport(name: string, summary: TrainingAnalysisSummary) {
  return unwrap<TrainingAnalysisAiReport>(request.post('/training-analysis/ai-report', { name, summary }))
}

export function exportTrainingReport(name: string) {
  return request.get('/training-analysis/export', { params: { name }, responseType: 'blob' })
}

export function deleteTrainingAnalysis(name: string) {
  return unwrap<{ deleted: number }>(request.delete(`/training-analysis/${encodeURIComponent(name)}`))
}

export function clearTrainingAnalyses() {
  return unwrap<{ deleted: number }>(request.delete('/training-analysis/clear'))
}
