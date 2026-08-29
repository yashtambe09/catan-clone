import genericPort from '../assets/ports/generic.svg'
import woodPort from '../assets/ports/wood.svg'
import brickPort from '../assets/ports/brick.svg'
import sheepPort from '../assets/ports/sheep.svg'
import wheatPort from '../assets/ports/wheat.svg'
import orePort from '../assets/ports/ore.svg'
import { edgePixel } from './boardGeometry'

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

  return (
    <image
      href={icon}
      x={px - ICON_SIZE / 2}
      y={py - ICON_SIZE / 2}
      width={ICON_SIZE}
      height={ICON_SIZE}
    />
  )
}

export default Port
