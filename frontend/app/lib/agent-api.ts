import { api } from './api'
import { AgentDeleteResponse, AgentEvent, AgentProjectLatestSessionResponse, AgentProjectSummary, AgentSessionResponse, AgentSessionStateResponse } from '@/types'

export type AgentTurnPayload = {
  message?: string
  input_mode?:
    | 'text'
    | 'multiple_choice'
    | 'start_mode'
    | 'focus_confirm'
    | 'quiz_ready'
    | 'dungeon_start'
    | 'dungeon_abort'
    | 'dungeon_dismiss'
  question_id?: string
  selected_option_id?: string
  selected_option_index?: number
}

export async function createAgentSession(query: string, learningStyle?: string | null) {
  return api.post<AgentSessionResponse>('/api/agent/sessions', {
    query,
    ...(learningStyle ? { learning_style: learningStyle } : {}),
  })
}

export async function getAgentSession(sessionId: string) {
  return api.get<AgentSessionStateResponse>(`/api/agent/sessions/${sessionId}`)
}

export async function listAgentProjects() {
  return api.get<AgentProjectSummary[]>(`/api/agent/projects`)
}

export async function getProjectLatestSession(projectId: string) {
  return api.get<AgentProjectLatestSessionResponse>(`/api/agent/projects/${projectId}/latest-session`)
}

export async function deleteAgentProject(projectId: string) {
  return api.delete<AgentDeleteResponse>(`/api/agent/projects/${projectId}`)
}

export async function listAgentSessionEvents(sessionId: string) {
  return api.get<AgentEvent[]>(`/api/agent/sessions/${sessionId}/events`)
}

export async function sendAgentMessage(sessionId: string, payload: AgentTurnPayload) {
  return api.post<AgentSessionResponse>(`/api/agent/sessions/${sessionId}/message`, payload)
}
