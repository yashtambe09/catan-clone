import genericPort from '../assets/ports/generic.svg'
import woodPort from '../assets/ports/wood.svg'
import brickPort from '../assets/ports/brick.svg'
import sheepPort from '../assets/ports/sheep.svg'
import wheatPort from '../assets/ports/wheat.svg'
import orePort from '../assets/ports/ore.svg'
import { edgePixel, vertexPixel } from './boardGeometry'

const PORT_ICONS = {
  wood: woodPort,
  brick: brickPort,
  sheep: sheepPort,
  wheat: wheatPort,
  ore: orePort,
}

const ICON_SIZE = 28
const OUTWARD_OFFSET = 0.9

function Port({ port, size, centroid }) {
  const { mx, my } = edgePixel(port.edge, size)
  const dx = mx - centroid.x
  const dy = my - centroid.y
  const dist = Math.hypot(dx, dy) || 1
  const px = mx + (dx / dist) * size * OUTWARD_OFFSET
  const py = my + (dy / dist) * size * OUTWARD_OFFSET
  const icon = port.resource ? PORT_ICONS[port.resource] : genericPort
  const color = port.resource ? `var(--resource-${port.resource})` : 'var(--color-muted)'

  const v1 = vertexPixel(port.vertices[0], size)
  const v2 = vertexPixel(port.vertices[1], size)

  return (
    <g>
      <polygon
        points={`${px},${py} ${v1.x},${v1.y} ${v2.x},${v2.y}`}
        fill={color}
        fillOpacity={0.12}
      />
      <line x1={px} y1={py} x2={v1.x} y2={v1.y} stroke={color} strokeWidth={2} strokeDasharray="1 4" strokeLinecap="round" />
      <line x1={px} y1={py} x2={v2.x} y2={v2.y} stroke={color} strokeWidth={2} strokeDasharray="1 4" strokeLinecap="round" />
      <image
        href={icon}
        x={px - ICON_SIZE / 2}
        y={py - ICON_SIZE / 2}
        width={ICON_SIZE}
        height={ICON_SIZE}
      />
    </g>
  )
}

export default Port
