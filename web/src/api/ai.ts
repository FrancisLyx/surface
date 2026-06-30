import { streamPost } from '../utils/streamRequest'
import { post } from '../utils/request'
import type { PageResponse } from './fund'

export type AiFundSummaryRequest = {
  fund_code: string
}

export type AiFundReportListRequest = {
  fund_code?: string
  page: number
  page_size: number
}

export type AiFundReportListItem = {
  id: number
  fund_code: string
  created_at: string
}

export type AiFundReportDetailResponse = AiFundReportListItem & {
  content: string
}

export function streamFundSummary(
  request: AiFundSummaryRequest,
  options: {
    signal?: AbortSignal
    onMessage: (message: string) => void
    onDone?: () => void
    onError?: (error: Error) => void
  },
) {
  return streamPost('/ai/funds/summary/stream', {
    data: request,
    signal: options.signal,
    onMessage: options.onMessage,
    onDone: options.onDone,
    onError: options.onError,
  })
}

export function listAiFundReports(request: AiFundReportListRequest) {
  return post<PageResponse<AiFundReportListItem>>('/ai/funds/reports/list', request)
}

export function getAiFundReportDetail(request: { id: number }) {
  return post<AiFundReportDetailResponse>('/ai/funds/reports/detail', request)
}
