import { useState } from 'react'
import {
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Form,
  Input,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import {
  getFundProfile,
  type FundDetailItem,
  type FundProfileRequest,
  type FundProfileResponse,
} from '../../api/fund'

function FundProfilePage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<FundProfileRequest>()
  const [profile, setProfile] = useState<FundProfileResponse>()
  const [loading, setLoading] = useState(false)

  const submit = async (values: FundProfileRequest) => {
    setLoading(true)
    try {
      const data = await getFundProfile({
        symbol: values.symbol.trim(),
        year: values.year.trim(),
      })
      setProfile(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Space orientation="vertical" size={16} className="page-stack">
      {contextHolder}
      <Card title="基金画像" className="tool-panel">
        <Form
          form={form}
          layout="inline"
          initialValues={{ symbol: '000001', year: '2024' }}
          onFinish={submit}
          className="query-form no-divider"
        >
          <Form.Item name="symbol" label="基金代码" rules={[{ required: true }]}>
            <Input placeholder="000001" />
          </Form.Item>
          <Form.Item name="year" label="年份" rules={[{ required: true }]}>
            <Input placeholder="2024" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
              查询
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {!profile ? (
        <Card className="tool-panel">
          <Empty className="empty-block" description="请输入基金代码和年份查询画像" />
        </Card>
      ) : (
        <>
          <ProfileSummary profile={profile} />
          <ProfileMetrics profile={profile} />

          <Card title="基本信息" className="tool-panel">
            <BasicInfoDescriptions items={profile.basic_info} />
          </Card>

          <Card title="费率信息" className="tool-panel">
            <Row gutter={[16, 16]}>
              {profile.fee_sections.map((section) => (
                <Col xs={24} xl={8} key={section.title}>
                  <Card size="small" title={section.title}>
                    <DynamicTable rows={section.rows} compact />
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <Card title="持仓明细" className="tool-panel">
                <DynamicTable
                  rows={profile.holdings}
                  priorityColumns={['股票代码', '股票名称', '占净值比例', '持股数', '持仓市值']}
                />
              </Card>
            </Col>
            <Col xs={24} xl={10}>
              <Card title="行业配置" className="tool-panel">
                <DynamicTable rows={profile.industry_allocations} priorityColumns={['行业类别', '占净值比例']} />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </Space>
  )
}

function ProfileSummary(props: { profile: FundProfileResponse }) {
  const name = pickInfoValue(props.profile.basic_info, ['基金名称', '基金简称']) || props.profile.symbol
  const fundType = pickInfoValue(props.profile.basic_info, ['基金类型']) || '类型未知'

  return (
    <Card className="tool-panel">
      <Row gutter={[16, 16]} align="middle">
        <Col flex="auto">
          <Typography.Text type="secondary">{props.profile.symbol}</Typography.Text>
          <Typography.Title level={2} className="profile-title">
            {name}
          </Typography.Title>
        </Col>
        <Col>
          <Space>
            <Tag color="blue">{fundType}</Tag>
            <Tag>{props.profile.year}</Tag>
          </Space>
        </Col>
      </Row>
      <Descriptions
        className="profile-summary-descriptions"
        size="small"
        column={{ xs: 1, md: 2, xl: 4 }}
        labelStyle={{ whiteSpace: 'nowrap', width: 88 }}
        contentStyle={{ minWidth: 0 }}
        items={[
          {
            key: 'manager',
            label: '基金经理',
            children: pickInfoValue(props.profile.basic_info, ['基金经理', '管理人']) || '-',
          },
          {
            key: 'startDate',
            label: '成立日期',
            children: pickInfoValue(props.profile.basic_info, ['成立日期', '基金成立日']) || '-',
          },
          {
            key: 'scale',
            label: '基金规模',
            children: pickInfoValue(props.profile.basic_info, ['基金规模', '资产规模']) || '-',
          },
          {
            key: 'company',
            label: '管理公司',
            children: pickInfoValue(props.profile.basic_info, ['基金管理人', '管理公司', '基金公司']) || '-',
          },
        ]}
      />
    </Card>
  )
}

function ProfileMetrics(props: { profile: FundProfileResponse }) {
  const topHolding = pickFirstRowValue(props.profile.holdings, ['股票名称', '证券名称']) || '-'
  const topIndustry = pickFirstRowValue(props.profile.industry_allocations, ['行业类别', '行业名称']) || '-'

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} xl={6}>
        <Card className="tool-panel">
          <Statistic title="持仓条目" value={props.profile.holdings.length} />
        </Card>
      </Col>
      <Col xs={24} sm={12} xl={6}>
        <Card className="tool-panel">
          <Statistic title="行业条目" value={props.profile.industry_allocations.length} />
        </Card>
      </Col>
      <Col xs={24} sm={12} xl={6}>
        <Card className="tool-panel">
          <Statistic title="第一重仓" value={topHolding} />
        </Card>
      </Col>
      <Col xs={24} sm={12} xl={6}>
        <Card className="tool-panel">
          <Statistic title="主要行业" value={topIndustry} />
        </Card>
      </Col>
    </Row>
  )
}

function BasicInfoDescriptions(props: { items: FundDetailItem[] }) {
  if (props.items.length === 0) {
    return <Empty className="empty-block" description="暂无基本信息" />
  }

  return (
    <Descriptions
      bordered
      size="small"
      column={{ xs: 1, md: 2, xl: 3 }}
      labelStyle={{
        width: 120,
        whiteSpace: 'nowrap',
      }}
      contentStyle={{
        minWidth: 0,
        wordBreak: 'break-word',
      }}
      items={props.items.map((item) => ({
        key: item.item,
        label: item.item,
        children: item.value || '-',
      }))}
    />
  )
}

function DynamicTable(props: { rows: Record<string, string>[]; priorityColumns?: string[]; compact?: boolean }) {
  if (props.rows.length === 0) {
    return <Empty className="empty-block" description="暂无数据" />
  }

  const keys = sortColumns(Object.keys(props.rows[0]), props.priorityColumns ?? [])
  const columns = keys.map((key) => ({
    title: key,
    dataIndex: key,
    key,
    ellipsis: true,
  }))

  return (
    <Table
      rowKey={(_, index) => String(index)}
      columns={columns}
      dataSource={props.rows}
      pagination={false}
      scroll={{ x: 'max-content' }}
      size={props.compact ? 'small' : 'middle'}
    />
  )
}

function sortColumns(keys: string[], priorityColumns: string[]) {
  return [
    ...priorityColumns.filter((key) => keys.includes(key)),
    ...keys.filter((key) => !priorityColumns.includes(key)),
  ]
}

function pickInfoValue(items: FundDetailItem[], labels: string[]) {
  return items.find((item) => labels.some((label) => item.item.includes(label)))?.value
}

function pickFirstRowValue(rows: Record<string, string>[], keys: string[]) {
  const firstRow = rows[0]
  if (!firstRow) {
    return ''
  }
  const key = keys.find((item) => firstRow[item])
  return key ? firstRow[key] : ''
}

export default FundProfilePage
