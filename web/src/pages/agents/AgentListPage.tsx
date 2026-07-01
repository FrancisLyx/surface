import { useEffect, useState } from 'react'
import { Card, List, Progress, Space, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { listAgents, type AgentListItem } from '../../api/agent'
import AgentRadar from './AgentRadar'
import { getAgentPersona } from './agentPersonas'

function AgentListPage() {
  const [agents, setAgents] = useState<AgentListItem[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    listAgents({ page: 1, page_size: 20 })
      .then((data) => setAgents(data.items))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title="选择智能体" className="tool-panel agent-select-panel">
      <List
        loading={loading}
        dataSource={agents}
        locale={{ emptyText: '暂无可用智能体' }}
        renderItem={(item, index) => {
          const persona = getAgentPersona(index)
          return (
            <List.Item>
              <button
                className={`agent-card agent-card-${persona.accent}`}
                type="button"
                onClick={() => navigate(`/agents/chat/${item.id}`)}
              >
                <div className={`agent-hero-stage agent-hero-${persona.accent}`}>
                  <img
                    className={`agent-avatar-image agent-avatar-${persona.imageMode || 'contain'}`}
                    src={persona.image}
                    alt={item.name}
                  />
                </div>
                <div className="agent-card-top">
                  <div className="agent-identity">
                    <Typography.Title level={4}>{item.name}</Typography.Title>
                    <Typography.Text>{persona.subtitle}</Typography.Text>
                  </div>
                  <Tag color={item.agent_type === 'fund' ? 'blue' : 'green'}>{item.agent_type}</Tag>
                </div>
                <Typography.Paragraph className="agent-persona-tone">
                  {persona.tone}
                </Typography.Paragraph>
                <div className="agent-quote">“{persona.quote}”</div>
                <Typography.Paragraph type="secondary" className="agent-description">
                  {item.description}
                </Typography.Paragraph>
                <AgentRadar persona={persona} />
                <div className="agent-stats">
                  {persona.stats.map((stat) => (
                    <div className="agent-stat" key={stat.label}>
                      <span>{stat.label}</span>
                      <Progress percent={stat.value} showInfo={false} size="small" />
                    </div>
                  ))}
                </div>
                <Space wrap className="agent-tags">
                  {persona.tags.map((tag) => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                  {item.is_builtin ? <Tag>系统内置</Tag> : <Tag>自定义</Tag>}
                </Space>
              </button>
            </List.Item>
          )
        }}
      />
    </Card>
  )
}

export default AgentListPage
