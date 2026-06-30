import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Space, Typography, message } from 'antd'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { getRegisterStatus, loginUser, type LoginRequest } from '../../api/user'
import { isAuthenticated, setStoredUser, setToken } from '../../utils/auth'
import { defaultRoutePath } from '../../utils/route'

function LoginPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [registrationEnabled, setRegistrationEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getRegisterStatus()
      .then((data) => setRegistrationEnabled(data.enabled))
      .catch(() => setRegistrationEnabled(false))
  }, [])

  if (isAuthenticated()) {
    return <Navigate to={defaultRoutePath} replace />
  }

  const submit = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const data = await loginUser(values)
      setToken(data.access_token)
      setStoredUser(data.user)
      navigate(defaultRoutePath, { replace: true })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      {contextHolder}
      <Card className="auth-card">
        <Space orientation="vertical" size={20} className="page-stack">
          <div>
            <Typography.Title level={2}>surface金融助手</Typography.Title>
            <Typography.Text type="secondary">登录后访问基金数据工作台</Typography.Text>
          </div>
          <Form layout="vertical" onFinish={submit}>
            <Form.Item name="account" label="账号" rules={[{ required: true, message: '请输入用户名、邮箱或手机号' }]}>
              <Input placeholder="用户名 / 邮箱 / 手机号" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form>
          {registrationEnabled ? (
            <Typography.Text type="secondary">
              没有账号？<Link to="/register">去注册</Link>
            </Typography.Text>
          ) : null}
        </Space>
      </Card>
    </div>
  )
}

export default LoginPage
