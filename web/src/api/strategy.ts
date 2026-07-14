import { get, post } from '../utils/request'
import type { AxiosRequestConfig } from 'axios'

export type StrategyLineKey = 'domestic' | 'overseas' | 'candidate'

export type MarketScriptKey =
  | 'domestic_story'
  | 'overseas_earnings'
  | 'hard_tech_siphon'
  | 'rotation_other'
  | 'unknown'

export type StrategyAnalyzeType =
  | 'market_structure_intraday_watch'
  | 'market_structure_discipline_advice'

export type StrategyEtfQuote = {
  line_key: StrategyLineKey
  line_name: string
  etf_code: string
  etf_name: string
  latest_price?: number | null
  iopv?: number | null
  discount_rate?: number | null
  change_amount?: number | null
  change_percent?: number | null
  volume?: number | null
  turnover?: number | null
  open_price?: number | null
  high_price?: number | null
  low_price?: number | null
  previous_close?: number | null
  trade_date: string
  update_time: string
  source: string
}

export type MarketScript = {
  key: MarketScriptKey
  label: string
  description: string
}

export type MarketStructureRealtimeResponse = {
  items: StrategyEtfQuote[]
  market_script: MarketScript
}

export type SectorWatchPoint = {
  label: string
  direction: 'strengthening' | 'weakening' | 'mixed' | 'no_data'
  observation: string
  average_change_percent?: number | null
  total_turnover?: number | null
  observed_etfs: StrategyEtfQuote[]
}

export type WatchPointSource = {
  etf_codes: string[]
  update_time: string
  provider: string
}

export type DisciplineRiskLevel = 'low' | 'medium' | 'high' | 'unknown'

export type DisciplineAdvice = {
  action: string
  risk_level: DisciplineRiskLevel
  position_hint: string
  reason: string
  evidence_quotes: string[]
  trigger_conditions: string[]
  invalidation_conditions: string[]
  risk_controls: string[]
}

export type MarketStructureWatchPointsResponse = {
  market_script: MarketScript
  sectors: SectorWatchPoint[]
  source: WatchPointSource
}

export type MarketStructureDisciplineAdviceResponse = {
  market_script: MarketScript
  advice: DisciplineAdvice
  source: WatchPointSource
}

export type StrategyAnalyzeResponse<TData> = {
  analyze_type: StrategyAnalyzeType
  strategy_code: string
  strategy_name: string
  agent_code: string
  agent_name: string
  data: TData
}

export type MarketStructureIntradayWatchAnalyzeData = {
  realtime: MarketStructureRealtimeResponse
  watch_points: MarketStructureWatchPointsResponse
}

export type MarketStructureDisciplineAdviceAnalyzeData = {
  discipline_advice: MarketStructureDisciplineAdviceResponse
}

export function analyzeStrategy<TData>(
  payload: {
    analyze_type: StrategyAnalyzeType
    params?: Record<string, unknown>
  },
  config?: AxiosRequestConfig,
) {
  return post<StrategyAnalyzeResponse<TData>>('/strategies/analyze', payload, {
    timeout: 60000,
    ...config,
  })
}

export function getMarketStructureRealtime(config?: AxiosRequestConfig) {
  return get<MarketStructureRealtimeResponse>(
    '/strategies/market-structure/realtime',
    config,
  )
}

export function getMarketStructureWatchPoints(
  params?: { market_script_key?: MarketScriptKey },
  config?: AxiosRequestConfig,
) {
  return get<MarketStructureWatchPointsResponse>(
    '/strategies/market-structure/watch-points',
    {
      ...config,
      params,
    },
  )
}

export function getMarketStructureDisciplineAdvice(
  params?: { market_script_key?: MarketScriptKey },
  config?: AxiosRequestConfig,
) {
  return get<MarketStructureDisciplineAdviceResponse>(
    '/strategies/market-structure/discipline-advice',
    {
      ...config,
      params,
    },
  )
}
