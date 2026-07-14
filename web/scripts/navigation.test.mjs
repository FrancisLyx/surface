import assert from 'node:assert/strict'
import {
  flattenLeafRoutes,
  getMenuRoutes,
  getSelectedMenuKey,
} from '../src/utils/navigation.ts'

const routes = [
  {
    path: '/funds',
    label: '基金列表',
    hidden: false,
    component: true,
  },
  {
    path: '/strategies',
    label: '策略分析',
    icon: true,
    children: [
      {
        path: '/strategies/market-structure',
        label: '市场格局风向标',
        icon: true,
        component: true,
      },
    ],
  },
  {
    path: '/hidden',
    label: '隐藏页面',
    hidden: true,
    component: true,
  },
]

assert.deepEqual(
  flattenLeafRoutes(routes).map((route) => route.path),
  ['/funds', '/strategies/market-structure', '/hidden'],
)
assert.deepEqual(
  getMenuRoutes(routes).map((route) => route.path),
  ['/funds', '/strategies'],
)
assert.equal(
  getSelectedMenuKey(routes, '/strategies/market-structure/detail', '/funds'),
  '/strategies/market-structure',
)
assert.equal(getSelectedMenuKey(routes, '/unknown', '/funds'), '/funds')
