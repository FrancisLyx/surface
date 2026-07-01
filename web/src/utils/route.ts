import {
  ApiOutlined,
  SettingOutlined,
  StarOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { createElement, type ComponentType, type ReactNode } from 'react'
import AiFundAnalysisPage from '../pages/ai/AiFundAnalysisPage'
import FundFavoritesPage from '../pages/funds/FundFavoritesPage'
import FundListPage from '../pages/funds/FundListPage'
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
    path: '/ai/fund-analysis',
    label: '自选分析',
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
