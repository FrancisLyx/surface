import {
  FundOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { appRoutes, defaultRoutePath } from '../utils/route'

const { Header, Sider, Content } = Layout

const menuItems: MenuProps['items'] = appRoutes.map((route) => ({
  key: route.path,
  label: route.label,
  icon: route.icon,
}))

function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  const selectedKey =
    appRoutes.find((item) => item.path === location.pathname)?.path ?? defaultRoutePath

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
