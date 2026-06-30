import {
  FundOutlined,
  FundProjectionScreenOutlined,
  LineChartOutlined,
  ProfileOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const menuRoutes = [
  { key: '/funds', label: '基金列表', icon: <UnorderedListOutlined /> },
  { key: '/funds/estimations', label: '净值估算', icon: <LineChartOutlined /> },
  { key: '/funds/detail', label: '基金详情', icon: <ProfileOutlined /> },
  { key: '/funds/value', label: '净值查询', icon: <FundProjectionScreenOutlined /> },
]

const menuItems: MenuProps['items'] = menuRoutes

function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  const selectedKey =
    menuRoutes.find((item) => item.key === location.pathname)?.key ?? '/funds'

  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <div className="brand">
          <FundOutlined />
          <div>
            <Typography.Title level={1}>surface金融管家</Typography.Title>
            <Typography.Text type="secondary">powered by AkShare fund API</Typography.Text>
          </div>
        </div>
      </Header>
      <Layout className="app-body">
        <Sider className="app-sider" width={220} breakpoint="lg" collapsedWidth={0}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
          />
        </Sider>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AdminLayout
