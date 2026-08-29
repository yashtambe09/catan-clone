import { useState } from 'react'

const RESOURCES = ['wood', 'brick', 'sheep', 'wheat', 'ore']

function GamePanel({ room, myName, act }) {
  const game = room.game
  const [vertex, setVertex] = useState('')
  const [edge, setEdge] = useState('')
  const [discardAmounts, setDiscardAmounts] = useState({})
  const [robberHex, setRobberHex] = useState('')
  const [stealFrom, setStealFrom] = useState('')

  const isMe = game.current_player === myName
  const myDiscard = game.pending_discards[myName]
  const me = game.players[myName]
  const settlementsToUpgrade = me ? me.settlements : []

  function submitVertex(action) {
    if (vertex) act(action, { vertex })
  }

  function submitEdge(action) {
    if (edge) act(action, { edge })
  }

  function submitDiscard() {
    const resources = Object.fromEntries(
      RESOURCES.map((r) => [r, Number(discardAmounts[r] || 0)]),
    )
    act('discard', { resources })
    setDiscardAmounts({})
  }

  function submitMoveRobber() {
    if (!robberHex) return
    const [q, r] = robberHex.split(',').map(Number)
    act('move_robber', { hex: [q, r], steal_from: stealFrom || null })
  }

  const otherPlayers = game.order.filter((n) => n !== myName)

  return (
    <div style={{ border: '1px solid gray', padding: 10, marginTop: 10 }}>
      <h3>Game</h3>
      <p>
        Phase: {game.phase} | Current: {game.current_player} | Turn: {game.turn_number}
      </p>
      {game.last_roll && <p>Last roll: {game.last_roll.join(' + ')}</p>}

      <ul>
        {game.order.map((n) => {
          const p = game.players[n]
          return (
            <li key={n}>
              {n} {n === myName && '(you)'} — VP {p.victory_points} —{' '}
              {RESOURCES.map((r) => `${r}:${p.resources[r]}`).join(' ')}
              {!p.connected && ' [disconnected]'}
            </li>
          )
        })}
      </ul>

      {isMe && (game.phase === 'setup_settlement' || game.phase === 'build') && (
        <div>
          <select value={vertex} onChange={(e) => setVertex(e.target.value)}>
            <option value="">-- pick vertex --</option>
            {game.legal.vertices.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
          <button
            onClick={() =>
              submitVertex(game.phase === 'setup_settlement' ? 'setup_settlement' : 'build_settlement')
            }
          >
            Place Settlement
          </button>
        </div>
      )}

      {isMe && (game.phase === 'setup_road' || game.phase === 'build') && (
        <div>
          <select value={edge} onChange={(e) => setEdge(e.target.value)}>
            <option value="">-- pick edge --</option>
            {game.legal.edges.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
          <button onClick={() => submitEdge(game.phase === 'setup_road' ? 'setup_road' : 'build_road')}>
            Place Road
          </button>
        </div>
      )}

      {isMe && game.phase === 'build' && settlementsToUpgrade.length > 0 && (
        <div>
          <select value={vertex} onChange={(e) => setVertex(e.target.value)}>
            <option value="">-- pick settlement --</option>
            {settlementsToUpgrade.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
          <button onClick={() => submitVertex('build_city')}>Build City</button>
        </div>
      )}

      {isMe && game.phase === 'roll' && <button onClick={() => act('roll', {})}>Roll Dice</button>}

      {isMe && game.phase === 'build' && <button onClick={() => act('end_turn', {})}>End Turn</button>}

      {myDiscard && (
        <div>
          <p>Discard {myDiscard} cards:</p>
          {RESOURCES.map((r) => (
            <label key={r}>
              {r}
              <input
                type="number"
                min="0"
                style={{ width: 40 }}
                value={discardAmounts[r] || ''}
                onChange={(e) => setDiscardAmounts({ ...discardAmounts, [r]: e.target.value })}
              />
            </label>
          ))}
          <button onClick={submitDiscard}>Discard</button>
        </div>
      )}

      {isMe && game.phase === 'move_robber' && (
        <div>
          <select value={robberHex} onChange={(e) => setRobberHex(e.target.value)}>
            <option value="">-- pick hex --</option>
            {room.board.hexes.map((h) => (
              <option key={h.coord.join(',')} value={h.coord.join(',')}>
                {h.coord.join(',')} ({h.terrain})
              </option>
            ))}
          </select>
          <select value={stealFrom} onChange={(e) => setStealFrom(e.target.value)}>
            <option value="">-- steal from nobody --</option>
            {otherPlayers.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <button onClick={submitMoveRobber}>Move Robber</button>
        </div>
      )}
    </div>
  )
}

export default GamePanel
