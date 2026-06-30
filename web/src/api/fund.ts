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

export type FavoriteFundItem = {
  id: number
  fund_code: string
  fund_name: string
  fund_type?: string | null
  created_at: string
}

export type FavoriteFundOptionItem = {
  fund_code: string
  fund_name: string
  fund_type?: string | null
}

export type FavoriteFundEstimationItem = FavoriteFundItem & {
  estimate_date?: string | null
  estimated_nav?: string | null
  estimated_growth_rate?: string | null
  published_date?: string | null
  published_nav?: string | null
  published_growth_rate?: string | null
  estimate_deviation?: string | null
  previous_nav_date?: string | null
  previous_nav?: string | null
  has_estimation: boolean
}

export type FavoriteFundReportExtreme = {
  fund_code: string
  fund_name: string
  rate: string
}

export type FavoriteFundReportSummary = {
  total: number
  estimated_count: number
  up_count: number
  down_count: number
  flat_count: number
  missing_count: number
  alert_count: number
  max_up?: FavoriteFundReportExtreme | null
  max_down?: FavoriteFundReportExtreme | null
}

export type FavoriteFundAlertItem = {
  fund_code: string
  fund_name: string
  level: string
  message: string
}

export type FavoriteFundReportResponse = {
  summary: FavoriteFundReportSummary
  alerts: FavoriteFundAlertItem[]
  page?: PageResponse<FavoriteFundEstimationItem> | null
}

export type FundEstimationItem = {
  code: string
  name: string
  estimate_date: string
  estimated_nav: string
  estimated_growth_rate: string
  published_date: string
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

export type FavoriteFundSearchRequest = FundSearchRequest

export type AddFavoriteFundRequest = {
  fund_code: string
  fund_name: string
  fund_type?: string | null
}

export type FavoriteFundCodeRequest = {
  fund_code: string
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

export function addFavoriteFund(request: AddFavoriteFundRequest) {
  return post<FavoriteFundItem>('/funds/favorites/add', request)
}

export function listFavoriteFunds(request: FavoriteFundSearchRequest) {
  return post<PageResponse<FavoriteFundItem>>('/funds/favorites/list', request)
}

export function listFavoriteFundOptions() {
  return post<FavoriteFundOptionItem[]>('/funds/favorites/options')
}

export function listFavoriteFundEstimations(request: FavoriteFundSearchRequest) {
  return post<PageResponse<FavoriteFundEstimationItem>>('/funds/favorites/estimations', request)
}

export function getFavoriteFundReport(request: FavoriteFundSearchRequest) {
  return post<FavoriteFundReportResponse>('/funds/favorites/report', request)
}

export function checkFavoriteFund(request: FavoriteFundCodeRequest) {
  return post<{ favorited: boolean }>('/funds/favorites/check', request)
}

export function removeFavoriteFund(request: FavoriteFundCodeRequest) {
  return post<{ removed: boolean }>('/funds/favorites/remove', request)
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
