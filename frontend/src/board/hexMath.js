const SQRT3 = Math.sqrt(3)

export function axialToPixel(q, r, size) {
  const x = size * (SQRT3 * q + (SQRT3 / 2) * r)
  const y = size * (1.5 * r)
  return { x, y }
}

export function hexCorners(cx, cy, size) {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30)
    points.push([cx + size * Math.cos(angle), cy + size * Math.sin(angle)])
  }
  return points
}
