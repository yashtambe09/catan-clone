// Mirrors backend/app/game/engine.py's COSTS — client-side only, for
// affordability greying. The server remains the sole source of truth.
export const COSTS = {
  road: { wood: 1, brick: 1 },
  settlement: { wood: 1, brick: 1, wheat: 1, sheep: 1 },
  city: { wheat: 2, ore: 3 },
  dev_card: { wheat: 1, sheep: 1, ore: 1 },
}

export function canAfford(resources, cost) {
  return Object.entries(cost).every(([r, n]) => (resources[r] || 0) >= n)
}
