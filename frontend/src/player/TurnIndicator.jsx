const MY_TURN_MESSAGES = {
  setup_settlement: 'Your turn — place a settlement',
  setup_road: 'Your turn — place a road',
  roll: 'Your turn — roll the dice',
  discard: 'Discard down to 7 cards',
  move_robber: 'Move the robber',
  build: 'Your turn — build or trade, then end turn',
}

function TurnIndicator({ isMe, currentPlayerName, phase }) {
  const message = isMe ? MY_TURN_MESSAGES[phase] || 'Your turn' : `Waiting on ${currentPlayerName}`

  return (
    <div
      className="turn-pulse"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 20px',
        borderRadius: 999,
        background: isMe ? 'var(--resource-wheat)' : 'var(--color-bg)',
        border: isMe ? 'none' : '1px solid var(--color-border-soft)',
        minWidth: 0,
        flexShrink: 1,
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: 'var(--color-accent)',
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontWeight: 700,
          fontSize: 14,
          color: 'var(--color-ink)',
          minWidth: 0,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {message}
      </span>
    </div>
  )
}

export default TurnIndicator
