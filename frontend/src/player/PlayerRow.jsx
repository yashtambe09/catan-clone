import DefaultAvatar from '../assets/avatars/default.svg?react'
import longestRoadBadge from '../assets/badges/longest-road.svg'
import largestArmyBadge from '../assets/badges/largest-army.svg'
import { colorForSeat } from './playerColors'
import { usePrevious } from '../hooks/usePrevious'

function cardCount(player) {
  if (typeof player.hand_size === 'number') return player.hand_size
  return Object.values(player.resources || {}).reduce((a, b) => a + b, 0)
}

function PlayerRow({ player, seatIndex, isViewer, isCurrentTurn, hasLongestRoad, hasLargestArmy, compact = false }) {
  const color = colorForSeat(seatIndex)
  const prevVP = usePrevious(player.victory_points)
  const vpGained = prevVP !== undefined && player.victory_points > prevVP

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: compact ? 6 : 10,
        padding: compact ? 6 : 10,
        borderRadius: 8,
        background: isCurrentTurn ? 'oklch(93% 0.05 85)' : 'transparent',
        flexShrink: 0,
      }}
    >
      <div
        className="avatar avatar-sm"
        style={{
          background: color,
          position: 'relative',
          width: compact ? 26 : undefined,
          height: compact ? 26 : undefined,
        }}
      >
        <DefaultAvatar width={compact ? 16 : 20} height={compact ? 16 : 20} style={{ color: 'var(--color-on-accent)' }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: 700,
            fontSize: compact ? 12 : 14,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            whiteSpace: compact ? 'nowrap' : undefined,
          }}
        >
          {isViewer ? 'You' : player.name}
          {hasLongestRoad && (
            <img className="badge-pop" src={longestRoadBadge} alt="Longest Road" width={16} height={16} />
          )}
          {hasLargestArmy && (
            <img className="badge-pop" src={largestArmyBadge} alt="Largest Army" width={16} height={16} />
          )}
          {!player.connected && (
            <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--color-muted)' }}>[disconnected]</span>
          )}
        </div>
        {!compact && <div style={{ fontSize: 12, color: 'var(--color-muted)' }}>{cardCount(player)} cards</div>}
      </div>
      <div
        key={player.victory_points}
        className={`avatar avatar-sm${vpGained ? ' resource-flash' : ''}`}
        style={{
          background: 'var(--resource-wheat)',
          color: 'var(--color-ink)',
          width: compact ? 22 : 26,
          height: compact ? 22 : 26,
          fontSize: compact ? 11 : 12,
        }}
      >
        {player.victory_points}
      </div>
    </div>
  )
}

export default PlayerRow
