import PlayerRow from './PlayerRow'

function PlayerDashboard({ game, myName }) {
  return (
    <div
      style={{
        width: 250,
        flexShrink: 0,
        boxSizing: 'border-box',
        padding: 20,
        borderRight: '1px solid var(--color-border-soft)',
        background: 'oklch(95% 0.015 85)',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        minHeight: 0,
        overflowY: 'auto',
      }}
    >
      <div className="eyebrow" style={{ marginBottom: 4 }}>
        Players
      </div>
      {game.order.map((name, i) => (
        <PlayerRow
          key={name}
          player={game.players[name]}
          seatIndex={i}
          isViewer={name === myName}
          isCurrentTurn={name === game.current_player}
          hasLongestRoad={game.longest_road_holder === name}
          hasLargestArmy={game.largest_army_holder === name}
        />
      ))}
    </div>
  )
}

export default PlayerDashboard
