import { LogoutOutlined, FundOutlined } from '@ant-design/icons'
import { Button, Layout, Menu, Space, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { clearToken, getStoredUser } from '../utils/auth'
import { getMenuRoutes, getSelectedMenuKey } from '../utils/navigation'
import { appRoutes, defaultRoutePath, type AppRoute } from '../utils/route'

const { Header, Sider, Content } = Layout

const visibleRoutes = getMenuRoutes(appRoutes)

function buildMenuItems(routes: AppRoute[]): MenuProps['items'] {
  return routes.map((route) => ({
    key: route.path,
    label: route.label,
    icon: route.icon,
    children: route.children?.length ? buildMenuItems(getMenuRoutes(route.children)) : undefined,
  }))
}

const menuItems = buildMenuItems(visibleRoutes)

function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = getStoredUser()

  const selectedKey = getSelectedMenuKey(appRoutes, location.pathname, defaultRoutePath)

  const logout = () => {
    clearToken()
    navigate('/login', { replace: true })
  }

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
        <Space className="header-user">
          <Typography.Text>{user?.username ?? '未登录'}</Typography.Text>
          <Button icon={<LogoutOutlined />} onClick={logout}>
            退出登录
          </Button>
        </Space>
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
