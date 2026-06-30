import { useEffect, useState } from 'react'
import { Card, Form, Space, Switch, Typography, message } from 'antd'
import { getRegistrationSetting, updateRegistrationSetting } from '../../api/settings'

function SystemSettingsPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const [enabled, setEnabled] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getRegistrationSetting()
      .then((data) => setEnabled(data.enabled))
      .catch((error) => messageApi.error(error instanceof Error ? error.message : '读取设置失败'))
      .finally(() => setLoading(false))
  }, [messageApi])

  const updateEnabled = async (checked: boolean) => {
    setLoading(true)
    try {
      const data = await updateRegistrationSetting({ enabled: checked })
      setEnabled(data.enabled)
      messageApi.success(data.enabled ? '已开启注册' : '已关闭注册')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '保存设置失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="系统设置" className="tool-panel settings-panel">
      {contextHolder}
      <Form layout="vertical">
        <Form.Item label="开放用户注册">
          <Space direction="vertical" size={8}>
            <Switch checked={enabled} loading={loading} onChange={updateEnabled} />
            <Typography.Text type="secondary">
              关闭后，未登录用户仍可访问登录页，但无法创建新账号。
            </Typography.Text>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default SystemSettingsPage
