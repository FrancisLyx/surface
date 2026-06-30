import { useMemo, useState } from 'react'
import { Button, Card, Form, Input, Space, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, SearchOutlined, StarFilled } from '@ant-design/icons'
import {
  addFavoriteFund,
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
  const [favoriteCodes, setFavoriteCodes] = useState<Set<string>>(new Set())
  const [favoriteLoadingCode, setFavoriteLoadingCode] = useState<string>()
  const [pagination, setPagination] = useState({ page: 1, page_size: 10 })

  const columns: ColumnsType<FundItem> = useMemo(
    () => [
      { title: '基金代码', dataIndex: 'code', width: 110, fixed: 'left' },
      { title: '基金简称', dataIndex: 'name', width: 220 },
      { title: '基金类型', dataIndex: 'fund_type', width: 160 },
      { title: '拼音缩写', dataIndex: 'abbreviation', width: 120 },
      { title: '拼音全称', dataIndex: 'pinyin', ellipsis: true },
      {
        title: '操作',
        key: 'action',
        width: 120,
        fixed: 'right',
        render: (_, record) => {
          const favorited = favoriteCodes.has(record.code)
          return (
            <Button
              type={favorited ? 'default' : 'primary'}
              icon={favorited ? <StarFilled /> : <PlusOutlined />}
              size="small"
              loading={favoriteLoadingCode === record.code}
              disabled={favorited}
              onClick={() => addToFavorite(record)}
            >
              {favorited ? '已自选' : '加自选'}
            </Button>
          )
        },
      },
    ],
    [favoriteCodes, favoriteLoadingCode],
  )

  const loadFunds = async (values: FundSearchRequest, page = pagination.page, pageSize = pagination.page_size) => {
    setLoading(true)
    try {
      const data = await listFunds({
        keyword: values.keyword?.trim() || undefined,
        page,
        page_size: pageSize,
      })
      setFundList(data)
      setPagination({ page, page_size: pageSize })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  const submit = async (values: FundSearchRequest) => {
    await loadFunds(values, 1, pagination.page_size)
  }

  const addToFavorite = async (fund: FundItem) => {
    setFavoriteLoadingCode(fund.code)
    try {
      await addFavoriteFund({
        fund_code: fund.code,
        fund_name: fund.name,
        fund_type: fund.fund_type,
      })
      setFavoriteCodes((previous) => new Set(previous).add(fund.code))
      messageApi.success('已加入自选')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '加入自选失败')
    } finally {
      setFavoriteLoadingCode(undefined)
    }
  }

  return (
    <Card title="基金列表查询" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ keyword: '华夏' }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="keyword" label="关键字">
          <Input allowClear autoComplete="off" placeholder="代码 / 简称 / 拼音" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
              查询
            </Button>
          </Space>
        </Form.Item>
      </Form>
      <PagedTable
        data={fundList}
        columns={columns}
        loading={loading}
        onPageChange={(page, pageSize) => loadFunds(form.getFieldsValue(), page, pageSize)}
      />
    </Card>
  )
}

export default FundListPage
