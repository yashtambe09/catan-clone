const PALETTE = [
  'var(--player-red)',
  'var(--player-blue)',
  'var(--player-orange)',
  'var(--player-cream)',
  'var(--player-green)',
  'var(--player-brown)',
]

export function colorForSeat(index) {
  return PALETTE[index % PALETTE.length]
}
