import { useEffect, useState } from 'react'
import { SearchOutlined } from '@ant-design/icons'
import { Button, Card, Drawer, Form, Input, Select, Table, Typography, message } from 'antd'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { getAgentReportDetail, listAgentReports, listAgents, type AgentListItem, type AgentReportListItem } from '../../api/agent'
import type { PageResponse } from '../../api/fund'
import MarkdownViewer from '../../components/MarkdownViewer'

function AgentReportPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<{ agent_id?: number; target_code?: string }>()
  const [agents, setAgents] = useState<AgentListItem[]>([])
  const [data, setData] = useState<PageResponse<AgentReportListItem>>()
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<string>('')
  const [detailTitle, setDetailTitle] = useState<string>('')

  const loadReports = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      const result = await listAgentReports({
        agent_id: values.agent_id || undefined,
        target_code: values.target_code?.trim() || undefined,
        page,
        page_size: pageSize,
      })
      setData(result)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '报告加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    listAgents({ page: 1, page_size: 20 })
      .then((result) => setAgents(result.items))
      .catch(() => setAgents([]))
  }, [])

  useEffect(() => {
    listAgentReports({
      page: 1,
      page_size: 10,
    })
      .then(setData)
      .catch(() => setData(undefined))
      .finally(() => setLoading(false))
  }, [])

  const openDetail = async (record: AgentReportListItem) => {
    setDetailLoading(true)
    setDetailTitle(record.title)
    try {
      const result = await getAgentReportDetail({ id: record.id })
      setDetail(result.content)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '报告详情加载失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const columns: ColumnsType<AgentReportListItem> = [
    { title: '标题', dataIndex: 'title', width: 240 },
    { title: '智能体', dataIndex: 'agent_name', width: 160 },
    { title: '对象', dataIndex: 'target_code', width: 120, render: (value) => value || '-' },
    {
      title: '生成时间',
      dataIndex: 'created_at',
      width: 190,
      render: (value: string) => new Date(value).toLocaleString(),
    },
  ]

  const pagination: TablePaginationConfig = {
    current: data?.page || 1,
    pageSize: data?.page_size || 10,
    total: data?.total || 0,
    showSizeChanger: true,
    onChange: (page, pageSize) => loadReports(page, pageSize),
  }

  return (
    <Card title="报告中心" className="tool-panel">
      {contextHolder}
      <Form form={form} layout="inline" className="query-form compact" onFinish={() => loadReports(1, data?.page_size || 10)}>
        <Form.Item name="agent_id" label="智能体">
          <Select
            allowClear
            className="agent-filter-select"
            placeholder="全部"
            options={agents.map((item) => ({ label: item.name, value: item.id }))}
          />
        </Form.Item>
        <Form.Item name="target_code" label="分析对象">
          <Input allowClear autoComplete="off" placeholder="基金代码" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" icon={<SearchOutlined />} htmlType="submit">
            查询
          </Button>
        </Form.Item>
      </Form>
      <Table
        rowKey="id"
        className="data-table"
        columns={columns}
        dataSource={data?.items || []}
        loading={loading}
        pagination={pagination}
        onRow={(record) => ({
          onClick: () => openDetail(record),
        })}
      />
      <Drawer
        width={820}
        title={detailTitle || '报告详情'}
        open={Boolean(detailTitle)}
        onClose={() => {
          setDetail('')
          setDetailTitle('')
        }}
      >
        {detailLoading ? (
          <Typography.Text type="secondary">加载中...</Typography.Text>
        ) : (
          <MarkdownViewer value={detail} />
        )}
      </Drawer>
    </Card>
  )
}

export default AgentReportPage
