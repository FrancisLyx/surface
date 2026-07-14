import assert from 'node:assert/strict'
import {
  MARKET_STRUCTURE_REFRESH_INTERVAL_MS,
  buildDisciplineControlItems,
  buildMarketLineViewModels,
  buildWatchSectorLabels,
} from '../src/pages/strategies/marketStructureConfig.ts'

const viewModels = buildMarketLineViewModels([
  {
    line_key: 'domestic',
    etf_code: '588710',
    etf_name: '科创半导体设备ETF华泰柏瑞',
    latest_price: 3.824,
    change_percent: -4.02,
    turnover: 1094325830,
    update_time: '2026-07-13 11:47:42+08:00',
  },
  {
    line_key: 'overseas',
    etf_code: '515880',
    etf_name: '通信ETF国泰',
    latest_price: 0.747,
    change_percent: -4.11,
    turnover: 2311196404,
    update_time: '2026-07-13 11:47:53+08:00',
  },
])

assert.equal(MARKET_STRUCTURE_REFRESH_INTERVAL_MS, 30_000)
assert.equal(viewModels[0].title, '国产硬科技线')
assert.equal(viewModels[0].quote.etf_code, '588710')
assert.equal(viewModels[0].quote.change_percent, -4.02)
assert.equal(viewModels[1].title, '海外算力链')
assert.equal(viewModels[1].quote.etf_code, '515880')
assert.deepEqual(
  buildMarketLineViewModels([]).map((item) => item.quote),
  [undefined, undefined],
)

assert.deepEqual(
  buildWatchSectorLabels({
    sectors: [
      {
        label: '机器人',
        direction: 'strengthening',
        observation: '机器人 当前整体走强，候选 ETF 平均涨跌幅 +3.00%。',
        average_change_percent: 3,
        total_turnover: 150000000,
        observed_etfs: [],
      },
      {
        label: '生物医药',
        direction: 'strengthening',
        observation: '生物医药 当前整体走强，候选 ETF 平均涨跌幅 +2.55%。',
        average_change_percent: 2.55,
        total_turnover: 43000000,
        observed_etfs: [],
      },
    ],
  }),
  ['机器人', '生物医药'],
)

assert.deepEqual(
  buildDisciplineControlItems({
    risk_controls: ['21 日线不抵抗就走'],
    trigger_conditions: ['两条核心 ETF 同步走弱'],
    invalidation_conditions: ['任一核心 ETF 放量翻红并站稳'],
  }).map((item) => item.title),
  ['触发条件', '风控动作', '复核条件'],
)
