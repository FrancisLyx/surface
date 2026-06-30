import {
  ApiOutlined,
  FundProjectionScreenOutlined,
  LineChartOutlined,
  ProfileOutlined,
  RadarChartOutlined,
  SettingOutlined,
  StarOutlined,
  TrophyOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { createElement, type ComponentType, type ReactNode } from 'react'
import AiFundAnalysisPage from '../pages/ai/AiFundAnalysisPage'
import FundDetailPage from '../pages/funds/FundDetailPage'
import FundEstimationsPage from '../pages/funds/FundEstimationsPage'
import FundFavoritesPage from '../pages/funds/FundFavoritesPage'
import FundListPage from '../pages/funds/FundListPage'
import FundProfilePage from '../pages/funds/FundProfilePage'
import FundRankPage from '../pages/funds/FundRankPage'
import FundValuePage from '../pages/funds/FundValuePage'
import SystemSettingsPage from '../pages/settings/SystemSettingsPage'

export type AppRoute = {
  path: string
  label: string
  icon: ReactNode
  component: ComponentType
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
    path: '/funds/estimations',
    label: '净值估算',
    icon: createElement(LineChartOutlined),
    component: FundEstimationsPage,
  },
  {
    path: '/funds/detail',
    label: '基金详情',
    icon: createElement(ProfileOutlined),
    component: FundDetailPage,
  },
  {
    path: '/funds/value',
    label: '净值查询',
    icon: createElement(FundProjectionScreenOutlined),
    component: FundValuePage,
  },
  {
    path: '/funds/rank',
    label: '基金排行',
    icon: createElement(TrophyOutlined),
    component: FundRankPage,
  },
  {
    path: '/funds/profile',
    label: '基金画像',
    icon: createElement(RadarChartOutlined),
    component: FundProfilePage,
  },
  {
    path: '/ai/fund-analysis',
    label: 'AI 分析',
    icon: createElement(ApiOutlined),
    component: AiFundAnalysisPage,
  },
  {
    path: '/settings',
    label: '系统设置',
    icon: createElement(SettingOutlined),
    component: SystemSettingsPage,
  },
]
