import { post } from '../utils/request'

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

export type FundRankItem = {
  code: string
  name: string
  fund_type: string
  unit_nav: string
  accumulated_nav: string
  daily_growth_rate: string
  weekly_growth_rate: string
  monthly_growth_rate: string
  quarterly_growth_rate: string
  half_year_growth_rate: string
  yearly_growth_rate: string
  current_year_growth_rate: string
  since_inception_growth_rate: string
  fee: string
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

export type FundFeeSection = {
  title: string
  rows: Record<string, string>[]
}

export type FundProfileResponse = {
  symbol: string
  year: string
  basic_info: FundDetailItem[]
  fee_sections: FundFeeSection[]
  holdings: Record<string, string>[]
  industry_allocations: Record<string, string>[]
}

export type FundSearchRequest = {
  keyword?: string
  page: number
  page_size: number
}

export type FundEstimationSearchRequest = FundSearchRequest & {
  category: string
}

export type FundRankSearchRequest = FundSearchRequest & {
  category: string
}

export type FundSymbolRequest = {
  symbol: string
}

export type FundProfileRequest = {
  symbol: string
  year: string
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

export function listFundRank(request: FundRankSearchRequest) {
  return post<PageResponse<FundRankItem>>('/funds/rank', request)
}

export function getFundDetail(request: FundSymbolRequest) {
  return post<FundDetailResponse>('/funds/detail', request)
}

export function getFundProfile(request: FundProfileRequest) {
  return post<FundProfileResponse>('/funds/profile', request)
}

export function getFundEstimation(request: FundSymbolRequest) {
  return post<FundEstimationItem>('/funds/estimation', request)
}

export function getFundValue(request: FundValueRequest) {
  return post<FundValueResponse>('/funds/value', request)
}
