import {
  AppstoreOutlined,
  ApiOutlined,
  FileTextOutlined,
  PartitionOutlined,
  RadarChartOutlined,
  SettingOutlined,
  StarOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { createElement, type ComponentType, type ReactNode } from 'react'
import AgentListPage from '../pages/agents/AgentListPage'
import AgentReportPage from '../pages/agents/AgentReportPage'
import AgentRunPage from '../pages/agents/AgentRunPage'
import AiFundAnalysisPage from '../pages/ai/AiFundAnalysisPage'
import FundFavoritesPage from '../pages/funds/FundFavoritesPage'
import FundListPage from '../pages/funds/FundListPage'
import SystemSettingsPage from '../pages/settings/SystemSettingsPage'
import MarketStructureStrategyPage from '../pages/strategies/MarketStructureStrategyPage'

export type AppRoute = {
  path: string
  label: string
  icon: ReactNode
  component?: ComponentType
  children?: AppRoute[]
  hidden?: boolean
}

export const defaultRoutePath = '/funds'

export const appRoutes: AppRoute[] = [
  {
    path: '/funds',
    label: '基金列表',
    icon: createElement(UnorderedListOutlined),
    component: FundListPage,
  },
  {
    path: '/funds/favorites',
    label: '我的自选',
    icon: createElement(StarOutlined),
    component: FundFavoritesPage,
  },
  {
    path: '/ai/fund-analysis',
    label: '自选分析',
    icon: createElement(ApiOutlined),
    component: AiFundAnalysisPage,
  },
  {
    path: '/strategies',
    label: '策略分析',
    icon: createElement(PartitionOutlined),
    children: [
      {
        path: '/strategies/market-structure',
        label: '市场格局风向标',
        icon: createElement(RadarChartOutlined),
        component: MarketStructureStrategyPage,
      },
    ],
  },
  {
    path: '/agents',
    label: '智能体',
    icon: createElement(AppstoreOutlined),
    component: AgentListPage,
  },
  {
    path: '/agents/chat/:agentId',
    label: '智能体对话',
    icon: createElement(AppstoreOutlined),
    component: AgentRunPage,
    hidden: true,
  },
  {
    path: '/agent-reports',
    label: '报告中心',
    icon: createElement(FileTextOutlined),
    component: AgentReportPage,
  },
  {
    path: '/settings',
    label: '系统设置',
    icon: createElement(SettingOutlined),
    component: SystemSettingsPage,
  },
]
