import {
  FundProjectionScreenOutlined,
  LineChartOutlined,
  ProfileOutlined,
  RadarChartOutlined,
  TrophyOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { createElement, type ComponentType, type ReactNode } from 'react'
import FundDetailPage from '../pages/funds/FundDetailPage'
import FundEstimationsPage from '../pages/funds/FundEstimationsPage'
import FundListPage from '../pages/funds/FundListPage'
import FundProfilePage from '../pages/funds/FundProfilePage'
import FundRankPage from '../pages/funds/FundRankPage'
import FundValuePage from '../pages/funds/FundValuePage'

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
]
