import { post } from './request'

export type PageResponse<T> = {
  page: number
  page_size: number
  total: number
  pages: number
  items: T[]
}

export type FundItem = {
  code: string
  abbreviation: string
  name: string
  fund_type: string
  pinyin: string
}

export type FundEstimationItem = {
  code: string
  name: string
  estimate_date: string
  estimated_nav: string
  estimated_growth_rate: string
  published_nav: string
  published_growth_rate: string
  estimate_deviation: string
  previous_nav_date: string
  previous_nav: string
}

export type FundDetailItem = {
  item: string
  value: string
}

export type FundDetailResponse = {
  symbol: string
  items: FundDetailItem[]
}

export type FundLatestNavItem = {
  code: string
  name: string
  nav_date: string
  unit_nav: string
  accumulated_nav: string
  daily_growth_value: string
  daily_growth_rate: string
  subscription_status: string
  redemption_status: string
  fee: string
}

export type FundValueResponse = {
  fund_code: string
  source: 'estimation' | 'daily'
  estimation: FundEstimationItem | null
  latest_nav: FundLatestNavItem | null
}

export type FundSearchRequest = {
  keyword?: string
  page: number
  page_size: number
}

export type FundEstimationSearchRequest = FundSearchRequest & {
  category: string
}

export type FundSymbolRequest = {
  symbol: string
}

export type FundValueRequest = {
  fund_code: string
  source: 'auto' | 'estimation' | 'daily'
}

export function listFunds(request: FundSearchRequest) {
  return post<PageResponse<FundItem>>('/funds/list', request)
}

export function listFundEstimations(request: FundEstimationSearchRequest) {
  return post<PageResponse<FundEstimationItem>>('/funds/estimations/search', request)
}

export function getFundDetail(request: FundSymbolRequest) {
  return post<FundDetailResponse>('/funds/detail', request)
}

export function getFundEstimation(request: FundSymbolRequest) {
  return post<FundEstimationItem>('/funds/estimation', request)
}

export function getFundValue(request: FundValueRequest) {
  return post<FundValueResponse>('/funds/value', request)
}
