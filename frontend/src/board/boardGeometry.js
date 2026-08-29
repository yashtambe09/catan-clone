import { axialToPixel } from './hexMath'

export function parseVertexId(vid) {
  return vid.split('|').map((part) => part.split(',').map(Number))
}

export function parseEdgeId(eid) {
  const [a, b] = eid.split('~')
  return [a, b]
}

export function vertexPixel(vid, size) {
  const coords = parseVertexId(vid)
  const pts = coords.map(([q, r]) => axialToPixel(q, r, size))
  return {
    x: pts.reduce((sum, p) => sum + p.x, 0) / pts.length,
    y: pts.reduce((sum, p) => sum + p.y, 0) / pts.length,
  }
}

export function edgePixel(eid, size) {
  const [a, b] = parseEdgeId(eid)
  const pa = vertexPixel(a, size)
  const pb = vertexPixel(b, size)
  return { ax: pa.x, ay: pa.y, bx: pb.x, by: pb.y, mx: (pa.x + pb.x) / 2, my: (pa.y + pb.y) / 2 }
}
