import { useMemo, useState } from 'react'
import { Button, Card, Form, Input, InputNumber, Select, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { SearchOutlined } from '@ant-design/icons'
import {
  listFundRank,
  type FundRankItem,
  type FundRankSearchRequest,
  type PageResponse,
} from '../../api/fund'
import { PagedTable, RateTag } from './FundWidgets'

function FundRankPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FundRankSearchRequest>()
  const [rankList, setRankList] = useState<PageResponse<FundRankItem>>()
  const [loading, setLoading] = useState(false)

  const columns: ColumnsType<FundRankItem> = useMemo(
    () => [
      { title: '基金代码', dataIndex: 'code', width: 110, fixed: 'left' },
      { title: '基金简称', dataIndex: 'name', width: 220 },
      { title: '基金类型', dataIndex: 'fund_type', width: 120 },
      { title: '单位净值', dataIndex: 'unit_nav', width: 110 },
      { title: '累计净值', dataIndex: 'accumulated_nav', width: 110 },
      {
        title: '日增长率',
        dataIndex: 'daily_growth_rate',
        width: 110,
        render: (value: string) => <RateTag value={value} />,
      },
      {
        title: '近1月',
        dataIndex: 'monthly_growth_rate',
        width: 110,
        render: (value: string) => <RateTag value={value} />,
      },
      {
        title: '近3月',
        dataIndex: 'quarterly_growth_rate',
        width: 110,
        render: (value: string) => <RateTag value={value} />,
      },
      {
        title: '近1年',
        dataIndex: 'yearly_growth_rate',
        width: 110,
        render: (value: string) => <RateTag value={value} />,
      },
      {
        title: '成立来',
        dataIndex: 'since_inception_growth_rate',
        width: 110,
        render: (value: string) => <RateTag value={value} />,
      },
      { title: '手续费', dataIndex: 'fee', width: 100 },
    ],
    [],
  )

  const submit = async (values: FundRankSearchRequest) => {
    setLoading(true)
    try {
      const data = await listFundRank({
        category: values.category,
        keyword: values.keyword?.trim() || undefined,
        page: values.page,
        page_size: values.page_size,
      })
      setRankList(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="基金排行" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ category: '全部', keyword: '华夏', page: 1, page_size: 10 }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="category" label="分类">
          <Select
            className="category-select"
            options={['全部', '股票型', '混合型', '债券型', '指数型', 'QDII', 'FOF'].map((value) => ({
              label: value,
              value,
            }))}
          />
        </Form.Item>
        <Form.Item name="keyword" label="关键字">
          <Input allowClear placeholder="代码 / 基金名称" />
        </Form.Item>
        <Form.Item name="page" label="页码" rules={[{ required: true }]}>
          <InputNumber min={1} />
        </Form.Item>
        <Form.Item name="page_size" label="每页" rules={[{ required: true }]}>
          <InputNumber min={1} max={200} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
            查询
          </Button>
        </Form.Item>
      </Form>
      <PagedTable data={rankList} columns={columns} loading={loading} />
    </Card>
  )
}

export default FundRankPage
