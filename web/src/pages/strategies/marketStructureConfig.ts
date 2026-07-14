import type {
  DisciplineAdvice,
  MarketStructureWatchPointsResponse,
  StrategyEtfQuote,
  StrategyLineKey,
} from '../../api/strategy'

export const MARKET_STRUCTURE_REFRESH_INTERVAL_MS = 30_000

export type MarketLineConfig = {
  title: string
  subtitle: string
  tone: StrategyLineKey
  signals: string[]
}

export type MarketLineViewModel = MarketLineConfig & {
  quote?: StrategyEtfQuote
}

export const MARKET_LINE_CONFIGS: MarketLineConfig[] = [
  {
    title: '国产硬科技线',
    subtitle: '半导体 / 华为链 / 交换机 / 连接器',
    tone: 'domestic',
    signals: ['封测', 'SoC', '交换机', '连接器', 'ETF 588710'],
  },
  {
    title: '海外算力链',
    subtitle: '算力 / 存储 / 液冷 / 电源 / 设备',
    tone: 'overseas',
    signals: ['达链', '谷歌链', '存储', '液冷电源', 'ETF 515880'],
  },
]

export function buildMarketLineViewModels(
  quotes: StrategyEtfQuote[],
): MarketLineViewModel[] {
  const quoteByLine = new Map(quotes.map((quote) => [quote.line_key, quote]))
  return MARKET_LINE_CONFIGS.map((line) => ({
    ...line,
    quote: quoteByLine.get(line.tone),
  }))
}

export function buildWatchSectorLabels(
  watchPoints: Pick<MarketStructureWatchPointsResponse, 'sectors'>,
) {
  return watchPoints.sectors.map((sector) => sector.label)
}

export function buildDisciplineControlItems(
  advice: Pick<
    DisciplineAdvice,
    'trigger_conditions' | 'risk_controls' | 'invalidation_conditions'
  >,
) {
  return [
    {
      title: '触发条件',
      items: advice.trigger_conditions,
    },
    {
      title: '风控动作',
      items: advice.risk_controls,
    },
    {
      title: '复核条件',
      items: advice.invalidation_conditions,
    },
  ]
}
