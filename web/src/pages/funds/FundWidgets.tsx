import { Descriptions, Empty, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type {
  FundDetailResponse,
  FundEstimationItem,
  FundLatestNavItem,
  FundValueResponse,
  PageResponse,
} from '../../api/fund'

export function PagedTable<T extends { code?: string; name?: string }>(props: {
  data?: PageResponse<T>
  columns: ColumnsType<T>
  loading: boolean
}) {
  return (
    <Table<T>
      rowKey={(record) => record.code ?? record.name ?? JSON.stringify(record)}
      columns={props.columns}
      dataSource={props.data?.items ?? []}
      loading={props.loading}
      scroll={{ x: 'max-content' }}
      pagination={
        props.data
          ? {
              current: props.data.page,
              pageSize: props.data.page_size,
              total: props.data.total,
              showSizeChanger: false,
            }
          : false
      }
      locale={{ emptyText: <Empty description="暂无数据" /> }}
      className="data-table"
    />
  )
}

export function KeyValueList(props: { detail?: FundDetailResponse }) {
  if (!props.detail) {
    return <Empty className="empty-block" description="请输入基金代码查询详情" />
  }

  return (
    <Descriptions
      bordered
      size="small"
      column={1}
      items={props.detail.items.map((item) => ({
        key: item.item,
        label: item.item,
        children: item.value || '-',
      }))}
    />
  )
}

export function EstimationCard(props: { estimation?: FundEstimationItem }) {
  if (!props.estimation) {
    return <Empty className="empty-block" description="请输入基金代码查询估算" />
  }

  const item = props.estimation
  return (
    <Descriptions
      bordered
      size="small"
      column={1}
      items={[
        { key: 'code', label: '基金代码', children: item.code },
        { key: 'name', label: '基金名称', children: item.name },
        { key: 'estimate_date', label: '估算日期', children: item.estimate_date },
        { key: 'estimated_nav', label: '估算净值', children: item.estimated_nav },
        {
          key: 'estimated_growth_rate',
          label: '估算增长率',
          children: <RateTag value={item.estimated_growth_rate} />,
        },
        { key: 'published_nav', label: '公布净值', children: item.published_nav },
        { key: 'previous_nav', label: '上一单位净值', children: item.previous_nav },
      ]}
    />
  )
}

export function FundValueResult(props: { value?: FundValueResponse }) {
  if (!props.value) {
    return <Empty className="empty-block" description="请输入基金代码查询净值" />
  }

  return (
    <div className="value-result">
      <Tag color={props.value.source === 'estimation' ? 'blue' : 'green'}>
        {props.value.source === 'estimation' ? '净值估算' : '公布净值'}
      </Tag>
      {props.value.estimation ? <EstimationCard estimation={props.value.estimation} /> : null}
      {props.value.latest_nav ? <LatestNavCard latestNav={props.value.latest_nav} /> : null}
    </div>
  )
}

function LatestNavCard(props: { latestNav: FundLatestNavItem }) {
  const item = props.latestNav
  return (
    <Descriptions
      bordered
      size="small"
      column={1}
      items={[
        { key: 'code', label: '基金代码', children: item.code },
        { key: 'name', label: '基金简称', children: item.name },
        { key: 'nav_date', label: '净值日期', children: item.nav_date },
        { key: 'unit_nav', label: '单位净值', children: item.unit_nav },
        { key: 'accumulated_nav', label: '累计净值', children: item.accumulated_nav },
        { key: 'daily_growth_value', label: '日增长值', children: item.daily_growth_value || '-' },
        {
          key: 'daily_growth_rate',
          label: '日增长率',
          children: <RateTag value={item.daily_growth_rate} />,
        },
        { key: 'subscription_status', label: '申购状态', children: item.subscription_status },
        { key: 'redemption_status', label: '赎回状态', children: item.redemption_status },
        { key: 'fee', label: '手续费', children: item.fee },
      ]}
    />
  )
}

export function RateTag(props: { value: string }) {
  const displayValue = formatRate(props.value)
  const normalized = displayValue.replace('%', '')
  const numeric = Number(normalized)
  const color = Number.isFinite(numeric) && numeric >= 0 ? 'red' : 'green'

  return <Tag color={displayValue !== '-' && displayValue !== '---' ? color : 'default'}>{displayValue}</Tag>
}

function formatRate(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return '-'
  }
  if (trimmed === '---' || trimmed.endsWith('%')) {
    return trimmed
  }

  const numeric = Number(trimmed)
  if (Number.isFinite(numeric)) {
    return `${trimmed}%`
  }

  return trimmed
}
