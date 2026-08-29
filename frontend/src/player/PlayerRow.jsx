import DefaultAvatar from '../assets/avatars/default.svg?react'
import longestRoadBadge from '../assets/badges/longest-road.svg'
import largestArmyBadge from '../assets/badges/largest-army.svg'
import { colorForSeat } from './playerColors'

function cardCount(player) {
  if (typeof player.hand_size === 'number') return player.hand_size
  return Object.values(player.resources || {}).reduce((a, b) => a + b, 0)
}

function PlayerRow({ player, seatIndex, isViewer, isCurrentTurn, hasLongestRoad, hasLargestArmy }) {
  const color = colorForSeat(seatIndex)

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: 10,
        borderRadius: 8,
        background: isCurrentTurn ? 'oklch(93% 0.05 85)' : 'transparent',
      }}
    >
      <div className="avatar avatar-sm" style={{ background: color, position: 'relative' }}>
        <DefaultAvatar width={20} height={20} style={{ color: 'var(--color-on-accent)' }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
          {isViewer ? 'You' : player.name}
          {hasLongestRoad && <img src={longestRoadBadge} alt="Longest Road" width={16} height={16} />}
          {hasLargestArmy && <img src={largestArmyBadge} alt="Largest Army" width={16} height={16} />}
          {!player.connected && (
            <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--color-muted)' }}>[disconnected]</span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-muted)' }}>{cardCount(player)} cards</div>
      </div>
      <div
        className="avatar avatar-sm"
        style={{ background: 'var(--resource-wheat)', color: 'var(--color-ink)', width: 26, height: 26, fontSize: 12 }}
      >
        {player.victory_points}
      </div>
    </div>
  )
}

export default PlayerRow
