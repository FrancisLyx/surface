import { useMemo, useState } from 'react'
import { Button, Card, Form, Input, InputNumber, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { SearchOutlined } from '@ant-design/icons'
import {
  listFunds,
  type FundItem,
  type FundSearchRequest,
  type PageResponse,
} from '../../api/fund'
import { PagedTable } from './FundWidgets'

function FundListPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FundSearchRequest>()
  const [fundList, setFundList] = useState<PageResponse<FundItem>>()
  const [loading, setLoading] = useState(false)

  const columns: ColumnsType<FundItem> = useMemo(
    () => [
      { title: '基金代码', dataIndex: 'code', width: 110, fixed: 'left' },
      { title: '基金简称', dataIndex: 'name', width: 220 },
      { title: '基金类型', dataIndex: 'fund_type', width: 160 },
      { title: '拼音缩写', dataIndex: 'abbreviation', width: 120 },
      { title: '拼音全称', dataIndex: 'pinyin', ellipsis: true },
    ],
    [],
  )

  const submit = async (values: FundSearchRequest) => {
    setLoading(true)
    try {
      const data = await listFunds({
        keyword: values.keyword?.trim() || undefined,
        page: values.page,
        page_size: values.page_size,
      })
      setFundList(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="基金列表查询" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ keyword: '华夏', page: 1, page_size: 10 }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="keyword" label="关键字">
          <Input allowClear placeholder="代码 / 简称 / 拼音" />
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
      <PagedTable data={fundList} columns={columns} loading={loading} />
    </Card>
  )
}

export default FundListPage
