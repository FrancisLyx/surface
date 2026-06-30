import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Space, Typography, message } from 'antd'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { getRegisterStatus, registerUser, type RegisterRequest } from '../../api/user'
import { isAuthenticated } from '../../utils/auth'
import { defaultRoutePath } from '../../utils/route'

type RegisterForm = RegisterRequest & {
  confirm_password: string
}

function RegisterPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [registrationEnabled, setRegistrationEnabled] = useState<boolean>()
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

  if (registrationEnabled === false) {
    return <Navigate to="/login" replace />
  }

  const submit = async (values: RegisterForm) => {
    if (values.password !== values.confirm_password) {
      messageApi.error('两次输入的密码不一致')
      return
    }

    const email = values.email?.trim()
    const phone = values.phone?.trim()
    if (!email && !phone) {
      messageApi.error('邮箱和手机号至少填写一项')
      return
    }

    setLoading(true)
    try {
      await registerUser({
        username: values.username.trim(),
        email: email || undefined,
        phone: phone || undefined,
        password: values.password,
      })
      messageApi.success('注册成功，请登录')
      navigate('/login', { replace: true })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '注册失败')
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
            <Typography.Title level={2}>创建账号</Typography.Title>
            <Typography.Text type="secondary">邮箱和手机号至少填写一项</Typography.Text>
          </div>
          <Form layout="vertical" onFinish={submit}>
            <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item name="email" label="邮箱" rules={[{ type: 'email', message: '请输入正确的邮箱格式' }]}>
              <Input placeholder="admin@example.com" />
            </Form.Item>
            <Form.Item name="phone" label="手机号">
              <Input placeholder="13800138000" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, message: '密码至少 6 位' }]}>
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            <Form.Item name="confirm_password" label="确认密码" rules={[{ required: true, message: '请再次输入密码' }]}>
              <Input.Password placeholder="请再次输入密码" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form>
          <Typography.Text type="secondary">
            已有账号？<Link to="/login">去登录</Link>
          </Typography.Text>
        </Space>
      </Card>
    </div>
  )
}

export default RegisterPage
