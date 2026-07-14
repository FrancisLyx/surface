import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Button, Card, Col, Row, Space, Tag, Typography } from 'antd'
import {
  AlertOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  LineChartOutlined,
  NodeIndexOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import {
  analyzeStrategy,
  type MarketScript,
  type MarketStructureDisciplineAdviceAnalyzeData,
  type MarketStructureDisciplineAdviceResponse,
  type MarketStructureIntradayWatchAnalyzeData,
  type MarketStructureRealtimeResponse,
  type MarketStructureWatchPointsResponse,
} from '../../api/strategy'
import {
  buildDisciplineControlItems,
  buildMarketLineViewModels,
  MARKET_STRUCTURE_REFRESH_INTERVAL_MS,
} from './marketStructureConfig'

const scripts = [
  {
    key: 'domestic_story',
    title: '国产替代主线',
    position: 'right-bottom',
    description: '国产线强、海外线弱，资金继续讲硬科技故事。',
  },
  {
    key: 'overseas_earnings',
    title: '业绩线回归',
    position: 'left-top',
    description: '海外线强、国产线弱，资金更重视业绩兑现。',
  },
  {
    key: 'hard_tech_siphon',
    title: '硬科技虹吸',
    position: 'right-top',
    description: '两条线同步走强，注意其他方向被抽血。',
  },
  {
    key: 'rotation_other',
    title: '轮动他处',
    position: 'left-bottom',
    description: '两条线同步走弱，观察机器人、生物医药等轮动方向。',
  },
]

function MarketStructureStrategyPage() {
  const [realtimeData, setRealtimeData] = useState<MarketStructureRealtimeResponse>()
  const [watchPointsData, setWatchPointsData] =
    useState<MarketStructureWatchPointsResponse>()
  const [disciplineData, setDisciplineData] =
    useState<MarketStructureDisciplineAdviceResponse>()
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const inFlightRef = useRef(false)

  const loadAnalysis = useCallback(
    async (options: { silent?: boolean; signal?: AbortSignal } = {}) => {
      if (inFlightRef.current) {
        return
      }

      inFlightRef.current = true
      if (!options.silent) {
        setLoading(true)
      }
      setErrorMessage('')

      try {
        const [intradayResult, disciplineResult] = await Promise.all([
          analyzeStrategy<MarketStructureIntradayWatchAnalyzeData>(
            { analyze_type: 'market_structure_intraday_watch', params: {} },
            { signal: options.signal },
          ),
          analyzeStrategy<MarketStructureDisciplineAdviceAnalyzeData>(
            { analyze_type: 'market_structure_discipline_advice', params: {} },
            { signal: options.signal },
          ),
        ])
        setRealtimeData(intradayResult.data.realtime)
        setWatchPointsData(intradayResult.data.watch_points)
        setDisciplineData(disciplineResult.data.discipline_advice)
      } catch (error) {
        if (!options.signal?.aborted) {
          setErrorMessage(error instanceof Error ? error.message : '策略分析加载失败')
        }
      } finally {
        inFlightRef.current = false
        if (!options.signal?.aborted) {
          setLoading(false)
        }
      }
    },
    [],
  )

  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => {
      loadAnalysis({ signal: controller.signal })
    })

    const timer = window.setInterval(() => {
      loadAnalysis({ silent: true })
    }, MARKET_STRUCTURE_REFRESH_INTERVAL_MS)

    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [loadAnalysis])

  const mainLines = useMemo(
    () => buildMarketLineViewModels(realtimeData?.items ?? []),
    [realtimeData],
  )
  const marketScript = realtimeData?.market_script

  return (
    <div className="strategy-page">
      <div className="strategy-header">
        <div>
          <Typography.Title level={2}>市场格局风向标</Typography.Title>
          <Typography.Text type="secondary">
            用前排风向标追踪两条硬科技主线，判断当前市场剧本和执行纪律。
          </Typography.Text>
        </div>
        <Space className="strategy-header-actions">
          {getLatestUpdateTime(realtimeData) ? (
            <Typography.Text type="secondary">
              更新：{getLatestUpdateTime(realtimeData)}
            </Typography.Text>
          ) : null}
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={() => loadAnalysis()}
          >
            刷新
          </Button>
          <Tag color="blue">策略分析</Tag>
        </Space>
      </div>

      <Alert
        showIcon
        type={marketScript ? getScriptAlertType(marketScript) : 'info'}
        className="strategy-alert"
        title={
          marketScript
            ? `当前剧本：${marketScript.label}`
            : '核心判断：先看主线强弱，再看前排是否撑住，最后按纪律处理持仓。'
        }
        description={marketScript?.description}
      />
      {errorMessage ? (
        <Alert showIcon type="warning" title={errorMessage} className="strategy-alert" />
      ) : null}

      <Row gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={9}>
          <div className="strategy-section">
            <div className="section-title">
              <BranchesOutlined />
              <Typography.Title level={3}>主线风向标</Typography.Title>
            </div>
            <div className="main-line-list">
              {mainLines.map((line) => (
                <div key={line.title} className={`main-line-card ${line.tone}`}>
                  <div className="main-line-card-header">
                    <div>
                      <Typography.Title level={4}>{line.title}</Typography.Title>
                      <Typography.Text type="secondary">{line.subtitle}</Typography.Text>
                    </div>
                    {line.quote ? (
                      <Tag color={getChangeTagColor(line.quote.change_percent)}>
                        {formatPercent(line.quote.change_percent)}
                      </Tag>
                    ) : (
                      <Tag>等待数据</Tag>
                    )}
                  </div>
                  {line.quote ? (
                    <div className="quote-grid">
                      <QuoteMetric label="ETF" value={`${line.quote.etf_code} ${line.quote.etf_name}`} />
                      <QuoteMetric label="最新价" value={formatNumber(line.quote.latest_price)} />
                      <QuoteMetric label="成交额" value={formatMoney(line.quote.turnover)} />
                      <QuoteMetric label="更新时间" value={line.quote.update_time || '-'} />
                    </div>
                  ) : null}
                  <div className="signal-tags">
                    {line.signals.map((signal) => (
                      <Tag key={signal}>{signal}</Tag>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Col>

        <Col xs={24} xl={9}>
          <div className="strategy-section">
            <div className="section-title">
              <NodeIndexOutlined />
              <Typography.Title level={3}>市场剧本四象限</Typography.Title>
            </div>
            <div className="script-matrix" aria-label="市场剧本四象限">
              <span className="axis axis-top">海外线强</span>
              <span className="axis axis-right">国产线强</span>
              <span className="axis axis-bottom">海外线弱</span>
              <span className="axis axis-left">国产线弱</span>
              {scripts.map((script) => (
                <div
                  key={script.title}
                  className={`script-cell ${script.position}${
                    marketScript?.key === script.key ? ' active' : ''
                  }`}
                >
                  <Typography.Text strong>{script.title}</Typography.Text>
                  <Typography.Text type="secondary">{script.description}</Typography.Text>
                </div>
              ))}
            </div>
          </div>
        </Col>

        <Col xs={24} xl={6}>
          <Card title="盘中观察点" className="strategy-watch-card">
            {watchPointsData ? (
              <Space orientation="vertical" size={12} className="watch-point-stack">
                {watchPointsData.sectors.map((sector) => (
                  <div key={sector.label} className="watch-sector">
                    <div className="watch-sector-header">
                      <Typography.Text strong>{sector.label}</Typography.Text>
                      <Tag color={getDirectionTagColor(sector.direction)}>
                        {getDirectionLabel(sector.direction)}
                      </Tag>
                    </div>
                    <Typography.Text type="secondary">
                      {sector.observation}
                    </Typography.Text>
                    <div className="quote-grid watch-quote-grid">
                      <QuoteMetric
                        label="候选均幅"
                        value={formatPercent(sector.average_change_percent)}
                      />
                      <QuoteMetric
                        label="候选成交额"
                        value={formatMoney(sector.total_turnover)}
                      />
                    </div>
                    <div className="signal-tags">
                      {sector.observed_etfs.slice(0, 4).map((quote) => (
                        <Tag key={quote.etf_code} color={getChangeTagColor(quote.change_percent)}>
                          {quote.etf_code} {formatPercent(quote.change_percent)}
                        </Tag>
                      ))}
                      {sector.observed_etfs.length === 0 ? <Tag>暂无匹配ETF</Tag> : null}
                    </div>
                  </div>
                ))}
              </Space>
            ) : (
              <Typography.Text type="secondary">等待盘中观察点数据</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>

      <div className="strategy-section discipline-section">
        <div className="section-title">
          <LineChartOutlined />
          <Typography.Title level={3}>操作纪律轨道</Typography.Title>
        </div>
        {disciplineData ? (
          <div className="discipline-panel">
            <div className="discipline-summary">
              <div>
                <Space size={8} wrap>
                  <Tag color={getRiskTagColor(disciplineData.advice.risk_level)}>
                    {getRiskLabel(disciplineData.advice.risk_level)}
                  </Tag>
                  <Typography.Text strong>
                    {disciplineData.advice.action}
                  </Typography.Text>
                </Space>
                <Typography.Text type="secondary">
                  {disciplineData.advice.position_hint}
                </Typography.Text>
              </div>
              <div className="signal-tags">
                {disciplineData.advice.evidence_quotes.map((quote) => (
                  <Tag key={quote}>{quote}</Tag>
                ))}
              </div>
            </div>
            <Typography.Text type="secondary">
              {disciplineData.advice.reason}
            </Typography.Text>
            <div className="discipline-track">
              {buildDisciplineControlItems(disciplineData.advice).map((group) => (
                <div key={group.title} className="discipline-step">
                  <span className="discipline-icon">
                    {getDisciplineGroupIcon(group.title)}
                  </span>
                  <Typography.Text strong>{group.title}</Typography.Text>
                  <ul className="discipline-list">
                    {group.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Typography.Text type="secondary">等待操作纪律数据</Typography.Text>
        )}
      </div>
    </div>
  )
}

function QuoteMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="quote-metric">
      <Typography.Text type="secondary">{label}</Typography.Text>
      <Typography.Text strong>{value}</Typography.Text>
    </div>
  )
}

function getLatestUpdateTime(data?: MarketStructureRealtimeResponse) {
  return data?.items.find((item) => item.update_time)?.update_time ?? ''
}

function getScriptAlertType(script: MarketScript) {
  if (script.key === 'hard_tech_siphon' || script.key === 'domestic_story') {
    return 'success'
  }
  if (script.key === 'rotation_other') {
    return 'warning'
  }
  return 'info'
}

function getChangeTagColor(value?: number | null) {
  if (value === undefined || value === null) {
    return 'default'
  }
  if (value > 0) {
    return 'red'
  }
  if (value < 0) {
    return 'green'
  }
  return 'default'
}

function getDirectionLabel(direction: MarketStructureWatchPointsResponse['sectors'][number]['direction']) {
  const labels = {
    strengthening: '走强',
    weakening: '走弱',
    mixed: '分化',
    no_data: '无数据',
  }
  return labels[direction]
}

function getDirectionTagColor(direction: MarketStructureWatchPointsResponse['sectors'][number]['direction']) {
  const colors = {
    strengthening: 'red',
    weakening: 'green',
    mixed: 'orange',
    no_data: 'default',
  }
  return colors[direction]
}

function getRiskLabel(
  riskLevel: MarketStructureDisciplineAdviceResponse['advice']['risk_level'],
) {
  const labels = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    unknown: '待确认',
  }
  return labels[riskLevel]
}

function getRiskTagColor(
  riskLevel: MarketStructureDisciplineAdviceResponse['advice']['risk_level'],
) {
  const colors = {
    low: 'green',
    medium: 'orange',
    high: 'red',
    unknown: 'default',
  }
  return colors[riskLevel]
}

function getDisciplineGroupIcon(title: string) {
  if (title === '触发条件') {
    return <CheckCircleOutlined />
  }
  if (title === '复核条件') {
    return <WarningOutlined />
  }
  return <AlertOutlined />
}

function formatPercent(value?: number | null) {
  if (value === undefined || value === null) {
    return '--'
  }
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatNumber(value?: number | null) {
  if (value === undefined || value === null) {
    return '--'
  }
  return value.toLocaleString('zh-CN', { maximumFractionDigits: 4 })
}

function formatMoney(value?: number | null) {
  if (value === undefined || value === null) {
    return '--'
  }
  if (Math.abs(value) >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}亿`
  }
  if (Math.abs(value) >= 10_000) {
    return `${(value / 10_000).toFixed(2)}万`
  }
  return formatNumber(value)
}

export default MarketStructureStrategyPage
