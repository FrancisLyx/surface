export type AgentPersona = {
  title: string
  subtitle: string
  avatar: string
  tone: string
  quote: string
  tags: string[]
  accent: string
  stats: Array<{ label: string; value: number }>
  radar: Array<{ label: string; value: number }>
  image: string
  imageMode?: 'contain' | 'cover'
}

const defaultPersona: AgentPersona = {
  title: '金融分析专家',
  subtitle: '稳健研究',
  avatar: '研',
  tone: '专业、审慎、数据优先',
  quote: '先看数据，再谈判断。',
  tags: ['数据分析', '风险评估'],
  accent: 'blue',
  stats: [
    { label: '稳健', value: 86 },
    { label: '进攻', value: 42 },
    { label: '风控', value: 92 },
  ],
  radar: [
    { label: '收益', value: 68 },
    { label: '进攻', value: 46 },
    { label: '速度', value: 58 },
    { label: '风控', value: 92 },
    { label: '研究', value: 88 },
    { label: '纪律', value: 86 },
  ],
  image: new URL('../../assets/柴犬.png', import.meta.url).href,
}

const personas: AgentPersona[] = [
  {
    title: '基金研究员',
    subtitle: '稳健派',
    avatar: '林',
    tone: '画像、估值、净值走势综合判断',
    quote: '不怕慢，就怕没看清楚风险。',
    tags: ['基金画像', '净值走势', '风控'],
    accent: 'blue',
    stats: [
      { label: '稳健', value: 90 },
      { label: '进攻', value: 48 },
      { label: '风控', value: 94 },
    ],
    radar: [
      { label: '收益', value: 70 },
      { label: '进攻', value: 48 },
      { label: '速度', value: 55 },
      { label: '风控', value: 94 },
      { label: '研究', value: 92 },
      { label: '纪律', value: 88 },
    ],
    image: new URL('../../assets/柴犬.png', import.meta.url).href,
  },
  {
    title: '组合巡检专家',
    subtitle: '巡检派',
    avatar: '夏',
    tone: '快速扫描自选组合的当日估值风险',
    quote: '组合里谁在动，先扫一遍再说。',
    tags: ['自选组合', '估值扫描', '提醒'],
    accent: 'green',
    stats: [
      { label: '稳健', value: 76 },
      { label: '速度', value: 88 },
      { label: '风控', value: 84 },
    ],
    radar: [
      { label: '收益', value: 62 },
      { label: '进攻', value: 58 },
      { label: '速度', value: 90 },
      { label: '风控', value: 84 },
      { label: '研究', value: 72 },
      { label: '纪律', value: 80 },
    ],
    image: new URL('../../assets/柴犬.png', import.meta.url).href,
  },
  {
    title: '股神阿佳',
    subtitle: '进攻派',
    avatar: '佳',
    tone: '说话直接，偏进攻，但不突破仓位和风控底线',
    quote: '草，机会是打出来的，但仓位不能上头。',
    tags: ['激进风格', '短线弹性', '仓位边界'],
    accent: 'red',
    stats: [
      { label: '进攻', value: 94 },
      { label: '速度', value: 86 },
      { label: '风控', value: 66 },
    ],
    radar: [
      { label: '收益', value: 90 },
      { label: '进攻', value: 96 },
      { label: '速度', value: 88 },
      { label: '风控', value: 62 },
      { label: '研究', value: 74 },
      { label: '纪律', value: 58 },
    ],
    image: new URL('../../assets/aj.jpg', import.meta.url).href,
    imageMode: 'cover',
  },
]

export function getAgentPersona(index?: number) {
  return typeof index === 'number' ? personas[index] || defaultPersona : defaultPersona
}
