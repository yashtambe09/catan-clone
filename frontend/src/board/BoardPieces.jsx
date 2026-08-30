import { useMemo } from 'react'
import { vertexPixel, edgePixel } from './boardGeometry'
import { colorForSeat } from '../player/playerColors'
import SettlementIcon from '../assets/pieces/settlement.svg?react'
import CityIcon from '../assets/pieces/city.svg?react'
import RoadIcon from '../assets/pieces/road.svg?react'

function BoardPieces({ game, size }) {
  const { vertexPieces, edgeRoads } = useMemo(() => {
    const vertexPieces = new Map()
    const edgeRoads = new Map()
    game.order.forEach((name, seat) => {
      const p = game.players[name]
      if (!p) return
      ;(p.roads || []).forEach((eid) => edgeRoads.set(eid, { seat }))
      ;(p.settlements || []).forEach((vid) => vertexPieces.set(vid, { type: 'settlement', seat }))
      ;(p.cities || []).forEach((vid) => vertexPieces.set(vid, { type: 'city', seat }))
    })
    return { vertexPieces, edgeRoads }
  }, [game.players, game.order])

  return (
    <>
      {/* Dilates each piece's silhouette and floods it with a dark outline
          color behind the original art, so pieces read clearly against the
          painterly tile backgrounds instead of blending in. Two radii since
          settlement/city (40-48 unit viewBox, rendered ~22-26px) and road
          (16-unit-tall viewBox, rendered at native 16px) scale down by very
          different factors - same radius would give roads a much heavier
          outline than settlements/cities. */}
      <defs>
        <filter id="piece-outline" x="-50%" y="-50%" width="200%" height="200%">
          <feMorphology in="SourceAlpha" operator="dilate" radius="2" result="dilated" />
          <feFlood floodColor="oklch(25% 0.02 60)" result="outlineColor" />
          <feComposite in="outlineColor" in2="dilated" operator="in" result="outline" />
          <feMerge>
            <feMergeNode in="outline" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="road-outline" x="-50%" y="-50%" width="200%" height="200%">
          <feMorphology in="SourceAlpha" operator="dilate" radius="1.2" result="dilated" />
          <feFlood floodColor="oklch(25% 0.02 60)" result="outlineColor" />
          <feComposite in="outlineColor" in2="dilated" operator="in" result="outline" />
          <feMerge>
            <feMergeNode in="outline" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {[...edgeRoads.entries()].map(([eid, { seat }]) => {
        const { ax, ay, bx, by, mx, my } = edgePixel(eid, size)
        const angle = (Math.atan2(by - ay, bx - ax) * 180) / Math.PI
        const len = Math.hypot(bx - ax, by - ay)
        return (
          <g
            key={eid}
            className="piece-pop-in"
            transform={`translate(${mx},${my}) rotate(${angle})`}
            style={{ color: colorForSeat(seat), filter: 'url(#road-outline)' }}
          >
            <RoadIcon x={-len / 2} y={-8} width={len} height={16} preserveAspectRatio="none" />
          </g>
        )
      })}

      {[...vertexPieces.entries()].map(([vid, { type, seat }]) => {
        const { x, y } = vertexPixel(vid, size)
        const Icon = type === 'city' ? CityIcon : SettlementIcon
        const iconSize = type === 'city' ? 26 : 22
        return (
          <g key={vid} className="piece-pop-in" style={{ color: colorForSeat(seat), filter: 'url(#piece-outline)' }}>
            <Icon x={x - iconSize / 2} y={y - iconSize / 2} width={iconSize} height={iconSize} />
          </g>
        )
      })}
    </>
  )
}

export default BoardPieces
