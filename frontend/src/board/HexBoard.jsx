import { useState } from 'react'
import { axialToPixel, hexCorners } from './hexMath'
import { vertexPixel, edgePixel } from './boardGeometry'
import { useZoomPan } from './useZoomPan'
import Port from './Port'
import BoardPieces from './BoardPieces'
import RobberStealPicker from './RobberStealPicker'
import forestTile from '../assets/tiles/forest.png'
import hillsTile from '../assets/tiles/hills.png'
import pastureTile from '../assets/tiles/pasture.png'
import fieldsTile from '../assets/tiles/fields.png'
import mountainsTile from '../assets/tiles/mountains.png'
import desertTile from '../assets/tiles/desert.png'
import robberIcon from '../assets/pieces/robber.svg'
import number2 from '../assets/numbers/2.png'
import number3 from '../assets/numbers/3.png'
import number4 from '../assets/numbers/4.png'
import number5 from '../assets/numbers/5.png'
import number6 from '../assets/numbers/6.png'
import number8 from '../assets/numbers/8.png'
import number9 from '../assets/numbers/9.png'
import number10 from '../assets/numbers/10.png'
import number11 from '../assets/numbers/11.png'
import number12 from '../assets/numbers/12.png'

const HEX_SIZE = 50
// The tile PNGs (settlerstiles pack) are near-flush pointy-top hexagons
// (219x256, ratio matches sqrt(3)/2 almost exactly), unlike the old SVGs'
// square 200x200 canvas with an inscribed hex - so they're sized directly
// to the real hex bounding box rather than scaled via a viewbox constant.
const TILE_RENDER_WIDTH = HEX_SIZE * Math.sqrt(3)
const TILE_RENDER_HEIGHT = HEX_SIZE * 2
const NUMBER_TOKEN_SIZE = 34

const TILE_ASSETS = {
  forest: forestTile,
  hills: hillsTile,
  pasture: pastureTile,
  fields: fieldsTile,
  mountains: mountainsTile,
  desert: desertTile,
}

const NUMBER_ASSETS = {
  2: number2,
  3: number3,
  4: number4,
  5: number5,
  6: number6,
  8: number8,
  9: number9,
  10: number10,
  11: number11,
  12: number12,
}

function HexBoard({ board, game, myName, act, playingKnight, playingRoadBuilding, onRoadBuildingDone }) {
  const [selectedRobberHex, setSelectedRobberHex] = useState(null)
  const [roadBuildingPicks, setRoadBuildingPicks] = useState([])
  const { transform, viewportRef, hasDraggedRef, reset, handlers } = useZoomPan()
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768
  const vertexHitRadius = isMobile ? 16 : 9
  const edgeHitWidth = isMobile ? 26 : 16

  const centers = board.hexes.map((hex) => {
    const [q, r] = hex.coord
    return { hex, ...axialToPixel(q, r, HEX_SIZE) }
  })

  const xs = centers.map((c) => c.x)
  const ys = centers.map((c) => c.y)
  const pad = HEX_SIZE * 2
  const minX = Math.min(...xs) - pad
  const minY = Math.min(...ys) - pad
  const width = Math.max(...xs) - minX + pad
  const height = Math.max(...ys) - minY + pad
  const centroid = {
    x: xs.reduce((a, b) => a + b, 0) / xs.length,
    y: ys.reduce((a, b) => a + b, 0) / ys.length,
  }

  const [robberQ, robberR] = board.robber

  const isMe = Boolean(game && myName && game.current_player === myName)
  const me = game?.players?.[myName]
  const legalVertices = game?.legal?.vertices || []
  const legalEdges = game?.legal?.edges || []
  const showVertexTargets = isMe && game && (game.phase === 'setup_settlement' || game.phase === 'build')
  const showEdgeTargets =
    isMe && game && (game.phase === 'setup_road' || game.phase === 'build' || playingRoadBuilding)
  const showRobberHexTargets = isMe && game && (game.phase === 'move_robber' || playingKnight)
  const pickedRoadEdges = new Set(roadBuildingPicks)

  function handleVertexClick(vid) {
    if (hasDraggedRef.current) return
    if (game.phase === 'setup_settlement') {
      act('setup_settlement', { vertex: vid })
    } else if (game.phase === 'build') {
      if (me?.settlements?.includes(vid)) {
        act('build_city', { vertex: vid })
      } else {
        act('build_settlement', { vertex: vid })
      }
    }
  }

  function handleEdgeClick(eid) {
    if (hasDraggedRef.current) return
    if (playingRoadBuilding) {
      if (pickedRoadEdges.has(eid)) return
      const next = [...roadBuildingPicks, eid]
      if (next.length >= 2) {
        act('play_road_building', { edges: next })
        setRoadBuildingPicks([])
        onRoadBuildingDone?.()
      } else {
        setRoadBuildingPicks(next)
      }
      return
    }
    if (game.phase === 'setup_road') {
      act('setup_road', { edge: eid })
    } else if (game.phase === 'build') {
      act('build_road', { edge: eid })
    }
  }

  function handleHexClick(coord) {
    if (hasDraggedRef.current) return
    if (!showRobberHexTargets) return
    setSelectedRobberHex(coord)
  }

  function handleStealConfirm(stealFrom) {
    if (playingKnight) {
      act('play_knight', { hex: selectedRobberHex, steal_from: stealFrom })
    } else {
      act('move_robber', { hex: selectedRobberHex, steal_from: stealFrom })
    }
    setSelectedRobberHex(null)
  }

  const otherPlayers = game ? game.order.filter((n) => n !== myName) : []

  return (
    <>
      <div
        ref={viewportRef}
        className="hexboard-viewport"
        style={{
          touchAction: 'none',
          overflow: 'hidden',
          width: '100%',
          height: '100%',
          maxWidth: 720,
          position: 'relative',
        }}
        {...handlers}
      >
      <svg
        viewBox={`${minX} ${minY} ${width} ${height}`}
        style={{
          width: '100%',
          height: '100%',
          maxHeight: '100%',
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
          transformOrigin: '0 0',
        }}
      >
        {centers.map(({ hex, x, y }) => {
          const isRobber = hex.coord[0] === robberQ && hex.coord[1] === robberR
          const isHot = hex.number === 6 || hex.number === 8
          const clickable = showRobberHexTargets

          return (
            <g
              key={`${hex.coord[0]},${hex.coord[1]}`}
              onClick={() => handleHexClick(hex.coord)}
              style={{ cursor: clickable ? 'pointer' : 'default' }}
            >
              <image
                href={TILE_ASSETS[hex.terrain]}
                x={x - TILE_RENDER_WIDTH / 2}
                y={y - TILE_RENDER_HEIGHT / 2}
                width={TILE_RENDER_WIDTH}
                height={TILE_RENDER_HEIGHT}
                preserveAspectRatio="none"
              />
              {clickable && (
                <polygon
                  points={hexCorners(x, y, HEX_SIZE).map((p) => p.join(',')).join(' ')}
                  fill="oklch(52% 0.16 35 / 0.15)"
                  stroke="var(--color-accent)"
                  strokeWidth="2"
                  strokeDasharray="4 3"
                />
              )}
              {hex.number !== null && (
                <>
                  <image
                    href={NUMBER_ASSETS[hex.number]}
                    x={x - NUMBER_TOKEN_SIZE / 2}
                    y={y - NUMBER_TOKEN_SIZE / 2}
                    width={NUMBER_TOKEN_SIZE}
                    height={NUMBER_TOKEN_SIZE}
                  />
                  {isHot && (
                    <circle
                      cx={x}
                      cy={y}
                      r={NUMBER_TOKEN_SIZE / 2 + 1}
                      fill="none"
                      stroke="var(--color-accent)"
                      strokeWidth="2.5"
                    />
                  )}
                </>
              )}
              {isRobber && (
                <image
                  key={`robber-${robberQ},${robberR}`}
                  href={robberIcon}
                  x={x - 10}
                  y={y - 20}
                  width={20}
                  height={26}
                  className="robber-drop"
                />
              )}
            </g>
          )
        })}

        {board.ports.map((port) => (
          <Port key={port.edge} port={port} size={HEX_SIZE} centroid={centroid} />
        ))}

        {game && <BoardPieces game={game} size={HEX_SIZE} />}

        {showVertexTargets &&
          legalVertices.map((vid) => {
            const { x, y } = vertexPixel(vid, HEX_SIZE)
            return (
              <circle
                key={vid}
                cx={x}
                cy={y}
                r={vertexHitRadius}
                fill="oklch(52% 0.16 35 / 0.2)"
                stroke="var(--color-accent)"
                strokeWidth="2"
                style={{ cursor: 'pointer' }}
                onClick={() => handleVertexClick(vid)}
              />
            )
          })}

        {isMe && game?.phase === 'build' && (me?.settlements || []).map((vid) => {
          const { x, y } = vertexPixel(vid, HEX_SIZE)
          return (
            <circle
              key={`city-${vid}`}
              cx={x}
              cy={y}
              r={11}
              fill="none"
              stroke="var(--resource-ore)"
              strokeWidth="3"
              strokeDasharray="3 2"
              style={{ cursor: 'pointer' }}
              onClick={() => handleVertexClick(vid)}
            />
          )
        })}

        {showEdgeTargets &&
          legalEdges
            .filter((eid) => !pickedRoadEdges.has(eid))
            .map((eid) => {
              const { ax, ay, bx, by } = edgePixel(eid, HEX_SIZE)
              return (
                <g key={eid} style={{ cursor: 'pointer' }} onClick={() => handleEdgeClick(eid)}>
                  <line x1={ax} y1={ay} x2={bx} y2={by} stroke="transparent" strokeWidth={edgeHitWidth} />
                  <line x1={ax} y1={ay} x2={bx} y2={by} stroke="oklch(52% 0.16 35 / 0.35)" strokeWidth={5} strokeLinecap="round" />
                </g>
              )
            })}

        {[...pickedRoadEdges].map((eid) => {
          const { ax, ay, bx, by } = edgePixel(eid, HEX_SIZE)
          return (
            <line
              key={`picked-${eid}`}
              x1={ax}
              y1={ay}
              x2={bx}
              y2={by}
              stroke="var(--resource-wood)"
              strokeWidth={5}
              strokeLinecap="round"
            />
          )
        })}
      </svg>

        <button
          className="btn btn-ghost"
          onClick={reset}
          style={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            fontSize: 12,
            padding: '4px 10px',
          }}
        >
          Reset view
        </button>
      </div>

      {selectedRobberHex && (
        <RobberStealPicker
          players={otherPlayers}
          onConfirm={handleStealConfirm}
          onCancel={() => setSelectedRobberHex(null)}
        />
      )}
    </>
  )
}

export default HexBoard
