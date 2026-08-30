import { useCallback, useEffect, useRef, useState } from 'react'

const MIN_SCALE = 0.75
const MAX_SCALE = 3
const DRAG_THRESHOLD = 5

function clampScale(scale) {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale))
}

export function useZoomPan() {
  const [transform, setTransform] = useState({ scale: 1, x: 0, y: 0 })
  // Kept in sync with `transform` on every update so event handlers can read
  // the current value synchronously - relying on setState's updater callback
  // for this would be unreliable, since React doesn't guarantee it runs
  // before the next line of code in a tight synchronous event sequence
  // (e.g. two pointerdowns dispatched back-to-back for a pinch start).
  const transformRef = useRef(transform)

  const applyTransform = useCallback((next) => {
    transformRef.current = next
    setTransform(next)
  }, [])

  const viewportRef = useRef(null)
  const hasDraggedRef = useRef(false)
  const pointersRef = useRef(new Map()) // pointerId -> {x, y}
  const dragStartRef = useRef(null) // {x, y} at last drag sample (single pointer)
  const pinchStartRef = useRef(null) // {dist, midX, midY, scale, x, y} at pinch start

  const reset = useCallback(() => {
    applyTransform({ scale: 1, x: 0, y: 0 })
  }, [applyTransform])

  const zoomAt = useCallback(
    (px, py, factor) => {
      const prev = transformRef.current
      const newScale = clampScale(prev.scale * factor)
      const wx = (px - prev.x) / prev.scale
      const wy = (py - prev.y) / prev.scale
      applyTransform({
        scale: newScale,
        x: px - wx * newScale,
        y: py - wy * newScale,
      })
    },
    [applyTransform],
  )

  const handleWheel = useCallback(
    (e) => {
      e.preventDefault()
      const rect = viewportRef.current.getBoundingClientRect()
      const px = e.clientX - rect.left
      const py = e.clientY - rect.top
      const factor = Math.exp(-e.deltaY * 0.001)
      zoomAt(px, py, factor)
    },
    [zoomAt],
  )

  // React's synthetic onWheel is attached passively, so e.preventDefault()
  // inside it is silently ignored (and logs a console error). Attaching a
  // native listener with {passive:false} is the standard workaround.
  useEffect(() => {
    const el = viewportRef.current
    if (!el) return undefined
    el.addEventListener('wheel', handleWheel, { passive: false })
    return () => el.removeEventListener('wheel', handleWheel)
  }, [handleWheel])

  const handlePointerDown = useCallback((e) => {
    // Cleared here (start of a new gesture), not on pointerup - the native
    // click that fires right after a drag-ending pointerup must still see
    // this as true, so it gets suppressed by the click handlers below.
    hasDraggedRef.current = false

    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    try {
      viewportRef.current?.setPointerCapture(e.pointerId)
    } catch {
      // Ignore - a pointerId not recognized as active (e.g. certain
      // synthetic/edge-case events) shouldn't abort gesture tracking.
    }

    if (pointersRef.current.size === 1) {
      dragStartRef.current = { x: e.clientX, y: e.clientY }
      pinchStartRef.current = null
    } else if (pointersRef.current.size === 2) {
      const pts = [...pointersRef.current.values()]
      const dist = Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y)
      const rect = viewportRef.current.getBoundingClientRect()
      const prev = transformRef.current
      pinchStartRef.current = {
        dist,
        midX: (pts[0].x + pts[1].x) / 2 - rect.left,
        midY: (pts[0].y + pts[1].y) / 2 - rect.top,
        scale: prev.scale,
        x: prev.x,
        y: prev.y,
      }
      dragStartRef.current = null
    }
  }, [])

  const handlePointerMove = useCallback((e) => {
    if (!pointersRef.current.has(e.pointerId)) return
    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY })

    if (pointersRef.current.size === 2 && pinchStartRef.current) {
      const pts = [...pointersRef.current.values()]
      const dist = Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y)
      const rect = viewportRef.current.getBoundingClientRect()
      const midX = (pts[0].x + pts[1].x) / 2 - rect.left
      const midY = (pts[0].y + pts[1].y) / 2 - rect.top
      const start = pinchStartRef.current
      const factor = dist / (start.dist || 1)
      const newScale = clampScale(start.scale * factor)
      const wx = (start.midX - start.x) / start.scale
      const wy = (start.midY - start.y) / start.scale
      hasDraggedRef.current = true
      applyTransform({
        scale: newScale,
        x: midX - wx * newScale,
        y: midY - wy * newScale,
      })
      return
    }

    if (pointersRef.current.size === 1 && dragStartRef.current) {
      const dx = e.clientX - dragStartRef.current.x
      const dy = e.clientY - dragStartRef.current.y
      if (Math.hypot(dx, dy) > DRAG_THRESHOLD) {
        hasDraggedRef.current = true
      }
      const prev = transformRef.current
      applyTransform({ ...prev, x: prev.x + dx, y: prev.y + dy })
      dragStartRef.current = { x: e.clientX, y: e.clientY }
    }
  }, [applyTransform])

  const handlePointerUp = useCallback((e) => {
    pointersRef.current.delete(e.pointerId)
    if (pointersRef.current.size < 2) pinchStartRef.current = null
    if (pointersRef.current.size === 0) dragStartRef.current = null
  }, [])

  return {
    transform,
    viewportRef,
    hasDraggedRef,
    reset,
    handlers: {
      onPointerDown: handlePointerDown,
      onPointerMove: handlePointerMove,
      onPointerUp: handlePointerUp,
      onPointerCancel: handlePointerUp,
    },
  }
}
