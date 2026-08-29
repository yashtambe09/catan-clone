import { axialToPixel, hexCorners } from './hexMath'

const HEX_SIZE = 50

function HexBoard({ board }) {
  const centers = board.hexes.map((hex) => {
    const [q, r] = hex.coord
    return { hex, ...axialToPixel(q, r, HEX_SIZE) }
  })

  const xs = centers.map((c) => c.x)
  const ys = centers.map((c) => c.y)
  const pad = HEX_SIZE * 1.5
  const minX = Math.min(...xs) - pad
  const minY = Math.min(...ys) - pad
  const width = Math.max(...xs) - minX + pad
  const height = Math.max(...ys) - minY + pad

  const [robberQ, robberR] = board.robber

  return (
    <svg viewBox={`${minX} ${minY} ${width} ${height}`} style={{ width: '100%', maxWidth: 720 }}>
      {centers.map(({ hex, x, y }) => {
        const points = hexCorners(x, y, HEX_SIZE)
          .map((p) => p.join(','))
          .join(' ')
        const isRobber = hex.coord[0] === robberQ && hex.coord[1] === robberR

        return (
          <g key={`${hex.coord[0]},${hex.coord[1]}`}>
            <polygon points={points} fill="none" stroke="black" />
            <text x={x} y={y - 8} textAnchor="middle" fontSize="10">
              {hex.terrain}
            </text>
            {hex.number !== null && (
              <text x={x} y={y + 12} textAnchor="middle" fontSize="14">
                {hex.number}
              </text>
            )}
            {isRobber && (
              <text x={x} y={y + 26} textAnchor="middle" fontSize="9">
                robber
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export default HexBoard
