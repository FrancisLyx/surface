import { post } from '../utils/request'
import { streamPost } from '../utils/streamRequest'
import type { PageResponse } from './fund'

export type AgentListItem = {
  id: number
  name: string
  agent_type: string
  description: string
  enabled: boolean
  is_builtin: boolean
}

export type AgentReportListItem = {
  id: number
  agent_id: number
  agent_name: string
  run_id: number
  title: string
  target_type: string
  target_code?: string | null
  created_at: string
}

export type AgentReportDetailResponse = AgentReportListItem & {
  content: string
}

export type AgentConversationListItem = {
  id: number
  agent_id: number
  title: string
  target_type?: string | null
  target_code?: string | null
  created_at: string
  updated_at: string
}

export type AgentConversationMessageItem = {
  id: number
  role: 'user' | 'assistant'
  message_type: string
  content: string
  created_at: string
}

export type AgentConversationDetailResponse = AgentConversationListItem & {
  messages: AgentConversationMessageItem[]
}

export type AgentChatStreamRequest = {
  agent_id: number
  message: string
  conversation_id?: number | null
  fund_code?: string
}

export function listAgents(request: { page: number; page_size: number }) {
  return post<PageResponse<AgentListItem>>('/agents/list', request)
}

export function streamAgentChat(
  request: AgentChatStreamRequest,
  options: {
    signal?: AbortSignal
    onMessage: (message: string) => void
    onEvent?: (event: { event: string; data: string }) => void
    onDone?: () => void
    onError?: (error: Error) => void
  },
) {
  return streamPost('/agents/chat/stream', {
    data: request,
    signal: options.signal,
    onMessage: options.onMessage,
    onEvent: options.onEvent,
    onDone: options.onDone,
    onError: options.onError,
  })
}

export function listAgentReports(request: {
  agent_id?: number
  target_code?: string
  page: number
  page_size: number
}) {
  return post<PageResponse<AgentReportListItem>>('/agents/reports/list', request)
}

export function getAgentReportDetail(request: { id: number }) {
  return post<AgentReportDetailResponse>('/agents/reports/detail', request)
}

export function listAgentConversations(request: { agent_id: number; page: number; page_size: number }) {
  return post<PageResponse<AgentConversationListItem>>('/agents/conversations/list', request)
}

export function getAgentConversationDetail(request: { conversation_id: number }) {
  return post<AgentConversationDetailResponse>('/agents/conversations/detail', request)
}
