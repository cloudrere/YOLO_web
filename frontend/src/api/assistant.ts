import { request, unwrap } from './request'

export interface AssistantStatus {
  configured: boolean
  model: string
  base_url?: string
}

export interface AssistantChatResponse {
  answer: string
  model: string
  configured: boolean
}

export function getAssistantStatus() {
  return unwrap<AssistantStatus>(request.get('/assistant/status'))
}

export function askAssistant(question: string) {
  return unwrap<AssistantChatResponse>(request.post('/assistant/chat', { question }))
}
