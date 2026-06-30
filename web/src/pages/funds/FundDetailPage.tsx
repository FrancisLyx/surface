import { useState } from 'react'
import { Button, Card, Form, Input, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import {
  getFundDetail,
  getFundEstimation,
  type FundDetailResponse,
  type FundEstimationItem,
  type FundSymbolRequest,
} from '../../api/fund'
import { EstimationCard, KeyValueList } from './FundWidgets'

function FundDetailPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [detailForm] = Form.useForm<FundSymbolRequest>()
  const [estimationForm] = Form.useForm<FundSymbolRequest>()
  const [fundDetail, setFundDetail] = useState<FundDetailResponse>()
  const [fundEstimation, setFundEstimation] = useState<FundEstimationItem>()
  const [loadingKey, setLoadingKey] = useState<string>()

  const runRequest = async <T,>(key: string, task: () => Promise<T>, onSuccess: (data: T) => void) => {
    setLoadingKey(key)
    try {
      const data = await task()
      onSuccess(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoadingKey(undefined)
    }
  }

  const submitFundDetail = (values: FundSymbolRequest) => {
    runRequest('fund-detail', () => getFundDetail({ symbol: values.symbol.trim() }), setFundDetail)
  }

  const submitFundEstimation = (values: FundSymbolRequest) => {
    runRequest(
      'fund-estimation',
      () => getFundEstimation({ symbol: values.symbol.trim() }),
      setFundEstimation,
    )
  }

  return (
    <Card title="基金详情与估算" className="tool-panel">
      {contextHolder}
      <div className="split-grid">
        <Card size="small" title="基金详情">
          <Form
            form={detailForm}
            layout="inline"
            initialValues={{ symbol: '000001' }}
            onFinish={submitFundDetail}
            className="query-form compact"
          >
            <Form.Item name="symbol" label="基金代码" rules={[{ required: true }]}>
              <Input placeholder="000001" />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                htmlType="submit"
                loading={loadingKey === 'fund-detail'}
              >
                查询
              </Button>
            </Form.Item>
          </Form>
          <KeyValueList detail={fundDetail} />
        </Card>
        <Card size="small" title="单只估算">
          <Form
            form={estimationForm}
            layout="inline"
            initialValues={{ symbol: '000001' }}
            onFinish={submitFundEstimation}
            className="query-form compact"
          >
            <Form.Item name="symbol" label="基金代码" rules={[{ required: true }]}>
              <Input placeholder="000001" />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                htmlType="submit"
                loading={loadingKey === 'fund-estimation'}
              >
                查询
              </Button>
            </Form.Item>
          </Form>
          <EstimationCard estimation={fundEstimation} />
        </Card>
      </div>
    </Card>
  )
}

export default FundDetailPage
