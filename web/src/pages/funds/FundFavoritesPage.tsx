import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, Popconfirm, Row, Space, Statistic, Tag, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import {
  getFavoriteFundReport,
  removeFavoriteFund,
  type FavoriteFundEstimationItem,
  type FavoriteFundReportResponse,
  type FavoriteFundSearchRequest,
  type PageResponse,
} from '../../api/fund'
import { PagedTable, PlainRate, RateTag } from './FundWidgets'

function FundFavoritesPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FavoriteFundSearchRequest>()
  const [favoriteList, setFavoriteList] = useState<PageResponse<FavoriteFundEstimationItem>>()
  const [report, setReport] = useState<FavoriteFundReportResponse>()
  const [loading, setLoading] = useState(false)
  const [removingCode, setRemovingCode] = useState<string>()
  const [pagination, setPagination] = useState({ page: 1, page_size: 10 })

  const loadFavorites = useCallback(async (
    values: FavoriteFundSearchRequest,
    page = pagination.page,
    pageSize = pagination.page_size,
  ) => {
    setLoading(true)
    try {
      const data = await getFavoriteFundReport({
        keyword: values.keyword?.trim() || undefined,
        page,
        page_size: pageSize,
      })
      setReport(data)
      setFavoriteList(data.page ?? undefined)
      setPagination({ page, page_size: pageSize })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }, [messageApi, pagination.page, pagination.page_size])

  useEffect(() => {
    void loadFavorites(form.getFieldsValue(), 1, 10)
  }, [])

  const submit = async (values: FavoriteFundSearchRequest) => {
    await loadFavorites(values, 1, pagination.page_size)
  }

  const removeFavorite = async (fundCode: string) => {
    setRemovingCode(fundCode)
    try {
      await removeFavoriteFund({ fund_code: fundCode })
      messageApi.success('已移除自选')
      await loadFavorites(form.getFieldsValue(), pagination.page, pagination.page_size)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '移除失败')
    } finally {
      setRemovingCode(undefined)
    }
  }

  const columns: ColumnsType<FavoriteFundEstimationItem> = useMemo(
    () => [
      { title: '基金代码', dataIndex: 'fund_code', width: 120, fixed: 'left' },
      { title: '基金名称', dataIndex: 'fund_name', width: 220 },
      {
        title: '估算状态',
        dataIndex: 'has_estimation',
        width: 110,
        render: (value: boolean) => <Tag color={value ? 'blue' : 'default'}>{value ? '有估算' : '暂无'}</Tag>,
      },
      { title: '估算日期', dataIndex: 'estimate_date', width: 120, render: (value) => value || '-' },
      { title: '估算净值', dataIndex: 'estimated_nav', width: 120, render: (value) => value || '-' },
      {
        title: '估算增长率',
        dataIndex: 'estimated_growth_rate',
        width: 130,
        render: (value: string | null) => <RateTag value={value || '-'} />,
      },
      { title: '公布日期', dataIndex: 'published_date', width: 120, render: (value) => value || '-' },
      { title: '公布净值', dataIndex: 'published_nav', width: 120, render: (value) => value || '-' },
      {
        title: '公布日增长率',
        dataIndex: 'published_growth_rate',
        width: 140,
        render: (value: string | null) => <RateTag value={value || '-'} />,
      },
      {
        title: '估算偏差',
        dataIndex: 'estimate_deviation',
        width: 120,
        render: (value: string | null) => <PlainRate value={value} />,
      },
      { title: '上一净值日期', dataIndex: 'previous_nav_date', width: 130, render: (value) => value || '-' },
      { title: '上一单位净值', dataIndex: 'previous_nav', width: 130, render: (value) => value || '-' },
      { title: '基金类型', dataIndex: 'fund_type', width: 160, render: (value) => value || '-' },
      {
        title: '添加时间',
        dataIndex: 'created_at',
        width: 200,
        render: (value: string) => new Date(value).toLocaleString(),
      },
      {
        title: '操作',
        key: 'action',
        width: 120,
        fixed: 'right',
        render: (_, record) => (
          <Popconfirm
            title="移除自选"
            description={`确认移除 ${record.fund_name}？`}
            okText="移除"
            cancelText="取消"
            onConfirm={() => removeFavorite(record.fund_code)}
          >
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              loading={removingCode === record.fund_code}
            >
              移除
            </Button>
          </Popconfirm>
        ),
      },
    ],
    [loadFavorites, removingCode],
  )

  return (
    <Card title="我的自选" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{}}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="keyword" label="关键字">
          <Input allowClear autoComplete="off" placeholder="代码 / 名称 / 类型" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
              查询
            </Button>
          </Space>
        </Form.Item>
      </Form>
      {report ? (
        <div className="favorite-dashboard">
          <Row gutter={[12, 12]}>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="自选总数" value={report.summary.total} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="有估算" value={report.summary.estimated_count} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="上涨" value={report.summary.up_count} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="下跌" value={report.summary.down_count} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="暂无估算" value={report.summary.missing_count} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="提醒" value={report.summary.alert_count} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="最大涨幅" value={report.summary.max_up?.rate ?? '-'} />
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Statistic title="最大跌幅" value={report.summary.max_down?.rate ?? '-'} />
            </Col>
          </Row>
          {report.alerts.length ? (
            <div className="favorite-alerts">
              {report.alerts.slice(0, 4).map((item) => (
                <Alert
                  key={`${item.fund_code}-${item.message}`}
                  type="warning"
                  showIcon
                  message={`${item.fund_name} ${item.message}`}
                />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      <PagedTable
        data={favoriteList}
        columns={columns}
        loading={loading}
        rowKey={(record) => String(record.id)}
        onPageChange={(page, pageSize) => loadFavorites(form.getFieldsValue(), page, pageSize)}
      />
    </Card>
  )
}

export default FundFavoritesPage
