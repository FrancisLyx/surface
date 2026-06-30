import { useState } from 'react'
import { Button, Card, Form, Input, Select, Space, message } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import {
  getFundValue,
  type FundValueRequest,
  type FundValueResponse,
} from '../../api/fund'
import { FundValueResult } from './FundWidgets'

function FundValuePage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FundValueRequest>()
  const [fundValue, setFundValue] = useState<FundValueResponse>()
  const [loading, setLoading] = useState(false)

  const submit = async (values: FundValueRequest) => {
    setLoading(true)
    try {
      const data = await getFundValue({
        fund_code: values.fund_code.trim(),
        source: values.source,
      })
      setFundValue(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="按来源查询净值" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ fund_code: '110029', source: 'auto' }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="fund_code" label="基金代码" rules={[{ required: true }]}>
          <Input autoComplete="off" placeholder="110029" />
        </Form.Item>
        <Form.Item name="source" label="来源">
          <Select
            className="source-select"
            options={[
              { label: '自动', value: 'auto' },
              { label: '净值估算', value: 'estimation' },
              { label: '公布净值', value: 'daily' },
            ]}
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
              查询
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                form.resetFields()
                setFundValue(undefined)
              }}
            >
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
      <FundValueResult value={fundValue} />
    </Card>
  )
}

export default FundValuePage
