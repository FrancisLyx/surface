import type { AgentPersona } from './agentPersonas'

type AgentRadarProps = {
  persona: AgentPersona
}

function AgentRadar(props: AgentRadarProps) {
  const points = props.persona.radar.map((item, index) => {
    const angle = -90 + index * 60
    const radius = 46 * (item.value / 100)
    const x = 50 + radius * Math.cos((angle * Math.PI) / 180)
    const y = 50 + radius * Math.sin((angle * Math.PI) / 180)
    return `${x},${y}`
  })

  const labelPositions = props.persona.radar.map((item, index) => {
    const angle = -90 + index * 60
    const radius = 58
    return {
      ...item,
      x: 50 + radius * Math.cos((angle * Math.PI) / 180),
      y: 50 + radius * Math.sin((angle * Math.PI) / 180),
    }
  })

  return (
    <div className={`agent-radar agent-radar-${props.persona.accent}`}>
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <polygon className="agent-radar-grid outer" points="50,4 89.8,27 89.8,73 50,96 10.2,73 10.2,27" />
        <polygon className="agent-radar-grid middle" points="50,19 76.8,34.5 76.8,65.5 50,81 23.2,65.5 23.2,34.5" />
        <polygon className="agent-radar-grid inner" points="50,34 63.8,42 63.8,58 50,66 36.2,58 36.2,42" />
        <polygon className="agent-radar-shape" points={points.join(' ')} />
        {points.map((point) => {
          const [cx, cy] = point.split(',')
          return <circle className="agent-radar-dot" cx={cx} cy={cy} key={point} r="1.8" />
        })}
      </svg>
      {labelPositions.map((item) => (
        <span
          className="agent-radar-label"
          key={item.label}
          style={{ left: `${item.x}%`, top: `${item.y}%` }}
        >
          {item.label}
        </span>
      ))}
    </div>
  )
}

export default AgentRadar
