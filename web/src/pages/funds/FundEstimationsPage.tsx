import { useMemo, useState } from 'react'
import { Button, Card, Form, Input, Select, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { SearchOutlined } from '@ant-design/icons'
import {
  listFundEstimations,
  type FundEstimationItem,
  type FundEstimationSearchRequest,
  type PageResponse,
} from '../../api/fund'
import { PagedTable, PlainRate, RateTag } from './FundWidgets'

function FundEstimationsPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FundEstimationSearchRequest>()
  const [estimationList, setEstimationList] = useState<PageResponse<FundEstimationItem>>()
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, page_size: 10 })

  const columns: ColumnsType<FundEstimationItem> = useMemo(
    () => [
      { title: '基金代码', dataIndex: 'code', width: 110, fixed: 'left' },
      { title: '基金名称', dataIndex: 'name', width: 260 },
      { title: '估算日期', dataIndex: 'estimate_date', width: 130 },
      { title: '估算净值', dataIndex: 'estimated_nav', width: 120 },
      {
        title: '估算增长率',
        dataIndex: 'estimated_growth_rate',
        width: 130,
        render: (value: string) => <RateTag value={value} />,
      },
      { title: '公布日期', dataIndex: 'published_date', width: 120 },
      { title: '公布净值', dataIndex: 'published_nav', width: 120 },
      {
        title: '公布日增长率',
        dataIndex: 'published_growth_rate',
        width: 130,
        render: (value: string) => <RateTag value={value} />,
      },
      {
        title: '估算偏差',
        dataIndex: 'estimate_deviation',
        width: 120,
        render: (value: string) => <PlainRate value={value} />,
      },
      { title: '上一净值日期', dataIndex: 'previous_nav_date', width: 130 },
      { title: '上一单位净值', dataIndex: 'previous_nav', width: 130 },
    ],
    [],
  )

  const loadEstimations = async (
    values: FundEstimationSearchRequest,
    page = pagination.page,
    pageSize = pagination.page_size,
  ) => {
    setLoading(true)
    try {
      const data = await listFundEstimations({
        keyword: values.keyword?.trim() || undefined,
        page,
        page_size: pageSize,
        category: values.category,
      })
      setEstimationList(data)
      setPagination({ page, page_size: pageSize })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  const submit = async (values: FundEstimationSearchRequest) => {
    await loadEstimations(values, 1, pagination.page_size)
  }

  return (
    <Card title="净值估算列表" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ keyword: '华夏', category: '全部' }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="keyword" label="关键字">
          <Input allowClear placeholder="代码 / 基金名称" />
        </Form.Item>
        <Form.Item name="category" label="分类">
          <Select
            className="category-select"
            options={[
              '全部',
              '股票型',
              '混合型',
              '债券型',
              '指数型',
              'QDII',
              'ETF联接',
              'LOF',
              '场内交易基金',
            ].map((value) => ({ label: value, value }))}
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
            查询
          </Button>
        </Form.Item>
      </Form>
      <PagedTable
        data={estimationList}
        columns={columns}
        loading={loading}
        onPageChange={(page, pageSize) => loadEstimations(form.getFieldsValue(), page, pageSize)}
      />
    </Card>
  )
}

export default FundEstimationsPage
