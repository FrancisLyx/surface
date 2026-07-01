import { useEffect, useMemo, useRef, useState } from 'react'
import { HistoryOutlined, PauseCircleOutlined, SendOutlined } from '@ant-design/icons'
import { Button, Card, Collapse, Drawer, Input, List, Space, Tag, Typography, message } from 'antd'
import { useParams } from 'react-router-dom'
import {
  getAgentConversationDetail,
  listAgentConversations,
  listAgents,
  streamAgentChat,
  type AgentConversationListItem,
  type AgentListItem,
} from '../../api/agent'
import MarkdownViewer from '../../components/MarkdownViewer'
import { getAgentPersona } from './agentPersonas'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

type ToolCall = {
  tool_call_id: string
  tool_name: string
  input?: unknown
  status?: string
  summary?: string
  data?: unknown
}

type StreamMessageEvent = {
  type?: string
  content?: string
}

type ConversationEvent = {
  conversation_id?: number
}

const DEFAULT_QUESTIONS = [
  '帮我看一下今天适不适合操作',
  '这个基金主要风险在哪里？',
  '如果收盘前估值继续下跌，我该怎么处理？',
]

function AgentRunPage() {
  const { agentId = '' } = useParams()
  const [messageApi, contextHolder] = message.useMessage()
  const [agents, setAgents] = useState<AgentListItem[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [conversations, setConversations] = useState<AgentConversationListItem[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [input, setInput] = useState('')
  const [fundCode, setFundCode] = useState('')
  const [loading, setLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const assistantMessageIdRef = useRef<string>('')

  useEffect(() => {
    listAgents({ page: 1, page_size: 20 })
      .then((data) => setAgents(data.items))
      .catch(() => setAgents([]))
  }, [])

  const currentAgent = useMemo(
    () => agents.find((item) => String(item.id) === agentId),
    [agentId, agents],
  )
  const currentAgentIndex = useMemo(
    () => agents.findIndex((item) => String(item.id) === agentId),
    [agentId, agents],
  )
  const currentPersona = useMemo(() => getAgentPersona(currentAgentIndex), [currentAgentIndex])

  const loadConversations = async () => {
    if (!currentAgent) {
      return
    }
    setHistoryLoading(true)
    try {
      const result = await listAgentConversations({ agent_id: currentAgent.id, page: 1, page_size: 50 })
      setConversations(result.items)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '历史会话加载失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  const send = async (preset?: string) => {
    const content = (preset ?? input).trim()
    if (!currentAgent) {
      messageApi.warning('智能体不存在')
      return
    }
    if (!content) {
      messageApi.warning('请输入问题')
      return
    }

    abortControllerRef.current?.abort()
    const abortController = new AbortController()
    abortControllerRef.current = abortController
    const assistantId = createId('assistant')
    assistantMessageIdRef.current = assistantId
    setMessages((previous) => [
      ...previous,
      { id: createId('user'), role: 'user', content },
      { id: assistantId, role: 'assistant', content: '' },
    ])
    setToolCalls([])
    setInput('')
    setLoading(true)

    try {
      await streamAgentChat(
        {
          agent_id: currentAgent.id,
          message: content,
          conversation_id: conversationId,
          fund_code: fundCode.trim() || undefined,
        },
        {
          signal: abortController.signal,
          onMessage: () => undefined,
          onEvent: (event) => handleStreamEvent(event.event, event.data),
          onDone: () => {
            setLoading(false)
            void loadConversations()
          },
          onError: (error) => messageApi.error(error.message),
        },
      )
    } catch (error) {
      if (!abortController.signal.aborted) {
        messageApi.error(error instanceof Error ? error.message : '智能体回复失败')
      }
    } finally {
      if (!abortController.signal.aborted) {
        setLoading(false)
      }
    }
  }

  const stop = () => {
    abortControllerRef.current?.abort()
    setLoading(false)
  }

  const openHistory = () => {
    setHistoryOpen(true)
    void loadConversations()
  }

  const loadConversationDetail = async (id: number) => {
    setHistoryLoading(true)
    try {
      const detail = await getAgentConversationDetail({ conversation_id: id })
      setConversationId(detail.id)
      setFundCode(detail.target_code || '')
      setToolCalls([])
      setMessages(
        detail.messages.map((item) => ({
          id: String(item.id),
          role: item.role,
          content: item.content,
        })),
      )
      setHistoryOpen(false)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '会话详情加载失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleStreamEvent = (eventName: string, data: string) => {
    if (eventName === 'conversation') {
      const event = parseJson<ConversationEvent>(data)
      if (event?.conversation_id) {
        setConversationId(event.conversation_id)
      }
      return
    }

    if (eventName === 'message') {
      const event = parseJson<StreamMessageEvent>(data)
      const delta = event?.content ?? data
      if (delta) {
        appendAssistantContent(delta)
      }
      return
    }

    if (eventName === 'tool_call') {
      const call = parseJson<ToolCall>(data)
      if (call) {
        setToolCalls((previous) => upsertToolCall(previous, call))
      }
      return
    }

    if (eventName === 'tool_result') {
      const result = parseJson<Pick<ToolCall, 'tool_call_id' | 'status' | 'summary' | 'data'>>(data)
      if (result) {
        setToolCalls((previous) =>
          previous.map((item) =>
            item.tool_call_id === result.tool_call_id
              ? { ...item, status: result.status, summary: result.summary, data: result.data }
              : item,
          ),
        )
      }
      return
    }

    if (eventName === 'error') {
      const error = parseJson<{ message?: string }>(data)
      messageApi.error(error?.message || '智能体回复失败')
    }
  }

  const appendAssistantContent = (delta: string) => {
    const assistantId = assistantMessageIdRef.current
    setMessages((previous) =>
      previous.map((item) =>
        item.id === assistantId ? { ...item, content: `${item.content}${delta}` } : item,
      ),
    )
  }

  return (
    <Card
      title={
        <Space className="agent-run-title">
          <img
            className={`agent-run-avatar-image agent-avatar-${currentPersona.imageMode || 'contain'}`}
            src={currentPersona.image}
            alt={currentPersona.title}
          />
          <div>
            <Typography.Text strong>{currentAgent ? currentAgent.name : '智能体对话'}</Typography.Text>
            <Typography.Text type="secondary">{currentPersona.title} · {currentPersona.subtitle}</Typography.Text>
          </div>
        </Space>
      }
      extra={
        <Button icon={<HistoryOutlined />} disabled={!currentAgent} onClick={openHistory}>
          历史
        </Button>
      }
      className="tool-panel agent-chat-panel"
    >
      {contextHolder}
      <Drawer
        title="历史会话"
        placement="left"
        width={320}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      >
        <List
          loading={historyLoading}
          dataSource={conversations}
          locale={{ emptyText: '暂无历史会话' }}
          renderItem={(item) => (
            <List.Item>
              <button
                className={`agent-history-item${conversationId === item.id ? ' active' : ''}`}
                type="button"
                onClick={() => loadConversationDetail(item.id)}
              >
                <Typography.Text strong ellipsis>
                  {item.title}
                </Typography.Text>
                <Typography.Text type="secondary">
                  {item.target_code || '未指定基金'} · {new Date(item.updated_at).toLocaleString()}
                </Typography.Text>
              </button>
            </List.Item>
          )}
        />
      </Drawer>
      <div className="agent-chat-layout">
        <div className="agent-chat-main">
          <div className="agent-chat-messages">
            {messages.length ? (
              messages.map((item) => (
                <div className={`agent-chat-message agent-chat-message-${item.role}`} key={item.id}>
                  <div className="agent-chat-bubble">
                    {item.content ? (
                      item.role === 'assistant' ? <MarkdownViewer value={item.content} /> : item.content
                    ) : (
                      <Typography.Text type="secondary">思考中...</Typography.Text>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="agent-chat-empty">
                <Typography.Title level={4}>{currentAgent?.name || '智能体'}</Typography.Title>
                <Typography.Paragraph type="secondary">
                  直接提问，智能体会根据问题决定是否调用基金画像、估值和净值走势工具。
                </Typography.Paragraph>
                <Space wrap>
                  {DEFAULT_QUESTIONS.map((question) => (
                    <Button key={question} disabled={!currentAgent || loading} onClick={() => send(question)}>
                      {question}
                    </Button>
                  ))}
                </Space>
              </div>
            )}
          </div>
          <div className="agent-chat-inputbar">
            <Input
              className="agent-chat-fund-input"
              allowClear
              placeholder="基金代码，可选"
              value={fundCode}
              onChange={(event) => setFundCode(event.target.value)}
            />
            <Input.TextArea
              autoSize={{ minRows: 1, maxRows: 4 }}
              value={input}
              placeholder="输入你想问智能体的问题"
              onChange={(event) => setInput(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault()
                  void send()
                }
              }}
            />
            <Button type="primary" icon={<SendOutlined />} disabled={!currentAgent} loading={loading} onClick={() => send()}>
              发送
            </Button>
            <Button icon={<PauseCircleOutlined />} disabled={!loading} onClick={stop}>
              停止
            </Button>
          </div>
        </div>
        <div className="agent-chat-side">
          <Typography.Title level={5}>工具调用</Typography.Title>
          {toolCalls.length ? (
            <Collapse
              size="small"
              items={toolCalls.map((item) => ({
                key: item.tool_call_id,
                label: (
                  <Space>
                    <span>{item.tool_name}</span>
                    <Tag color={item.status === 'success' ? 'success' : 'processing'}>
                      {item.status || 'running'}
                    </Tag>
                  </Space>
                ),
                children: (
                  <Space direction="vertical" className="agent-tool-detail">
                    {item.summary ? <Typography.Text>{item.summary}</Typography.Text> : null}
                    <Typography.Text type="secondary">输入</Typography.Text>
                    <pre>{JSON.stringify(item.input ?? {}, null, 2)}</pre>
                    {item.data ? (
                      <>
                        <Typography.Text type="secondary">输出</Typography.Text>
                        <pre>{JSON.stringify(item.data, null, 2)}</pre>
                      </>
                    ) : null}
                  </Space>
                ),
              }))}
            />
          ) : (
            <Typography.Text type="secondary">需要数据时会自动调用工具</Typography.Text>
          )}
        </div>
      </div>
    </Card>
  )
}

function parseJson<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T
  } catch {
    return null
  }
}

function upsertToolCall(items: ToolCall[], call: ToolCall) {
  const index = items.findIndex((item) => item.tool_call_id === call.tool_call_id)
  if (index < 0) {
    return [...items, call]
  }
  return items.map((item) => (item.tool_call_id === call.tool_call_id ? { ...item, ...call } : item))
}

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export default AgentRunPage
