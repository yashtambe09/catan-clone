import { useState } from 'react'

const RESOURCES = ['wood', 'brick', 'sheep', 'wheat', 'ore']

function toCostMap(amounts) {
  return Object.fromEntries(RESOURCES.map((r) => [r, Number(amounts[r] || 0)]).filter(([, n]) => n > 0))
}

function ResourceAmounts({ amounts, onChange }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {RESOURCES.map((r) => (
        <div key={r} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, textTransform: 'capitalize' }}>
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: '50%',
                background: `var(--resource-${r})`,
                display: 'inline-block',
              }}
            />
            {r}
          </span>
          <input
            className="input"
            type="number"
            min="0"
            style={{ width: 56, padding: '6px 8px' }}
            value={amounts[r] || ''}
            onChange={(e) => onChange({ ...amounts, [r]: e.target.value })}
          />
        </div>
      ))}
    </div>
  )
}

function BankTrade({ bankRatios, act }) {
  const [give, setGive] = useState('wood')
  const [want, setWant] = useState('brick')
  const ratio = bankRatios?.[give] ?? 4

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12 }}>
      <span style={{ fontWeight: 700, fontSize: 14 }}>Bank Trade</span>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <select className="input" value={give} onChange={(e) => setGive(e.target.value)}>
          {RESOURCES.map((r) => (
            <option key={r} value={r}>
              {ratio}:1 {r}
            </option>
          ))}
        </select>
        <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>for</span>
        <select className="input" value={want} onChange={(e) => setWant(e.target.value)}>
          {RESOURCES.filter((r) => r !== give).map((r) => (
            <option key={r} value={r}>
              1 {r}
            </option>
          ))}
        </select>
      </div>
      <button
        className="btn btn-secondary"
        onClick={() => act('bank_trade', { give, want, count: 1 })}
      >
        Trade with Bank
      </button>
    </div>
  )
}

function ProposeTrade({ otherPlayers, act }) {
  const [give, setGive] = useState({})
  const [want, setWant] = useState({})
  const [target, setTarget] = useState('')

  function submit() {
    const giveMap = toCostMap(give)
    const wantMap = toCostMap(want)
    if (Object.keys(giveMap).length === 0 || Object.keys(wantMap).length === 0) return
    act('trade_propose', { give: giveMap, want: wantMap, target: target || null })
    setGive({})
    setWant({})
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12 }}>
      <span style={{ fontWeight: 700, fontSize: 14 }}>Propose Trade</span>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>
            You give
          </div>
          <ResourceAmounts amounts={give} onChange={setGive} />
        </div>
        <div style={{ flex: 1 }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>
            You want
          </div>
          <ResourceAmounts amounts={want} onChange={setWant} />
        </div>
      </div>
      <select className="input" value={target} onChange={(e) => setTarget(e.target.value)}>
        <option value="">Anyone</option>
        {otherPlayers.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
      <button className="btn btn-secondary" onClick={submit}>
        Propose Trade
      </button>
    </div>
  )
}

function ActiveTrade({ trade, myName, isCurrentPlayer, act }) {
  const [countering, setCountering] = useState(false)
  const [give, setGive] = useState({})
  const [want, setWant] = useState({})

  const isProposer = trade.proposer === myName
  const canRespond = !isProposer && (trade.target === null || trade.target === myName)
  const alreadyRejected = trade.rejected_by.includes(myName)

  function submitCounter() {
    const giveMap = toCostMap(give)
    const wantMap = toCostMap(want)
    if (Object.keys(giveMap).length === 0 || Object.keys(wantMap).length === 0) return
    act('trade_counter', { give: giveMap, want: wantMap })
    setCountering(false)
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12 }}>
      <span style={{ fontWeight: 700, fontSize: 14 }}>
        {isProposer ? 'Your offer' : `${trade.proposer}'s offer`}
        {trade.target && ` → ${trade.target}`}
      </span>
      <div style={{ fontSize: 13, color: 'var(--color-muted)' }}>
        Gives {Object.entries(trade.give).map(([r, n]) => `${n} ${r}`).join(', ')} for{' '}
        {Object.entries(trade.want).map(([r, n]) => `${n} ${r}`).join(', ')}
      </div>
      {trade.rejected_by.length > 0 && (
        <div style={{ fontSize: 12, color: 'var(--color-muted)' }}>
          Rejected by {trade.rejected_by.join(', ')}
        </div>
      )}

      {isProposer && (
        <button className="btn btn-destructive" onClick={() => act('trade_cancel', {})}>
          Cancel Trade
        </button>
      )}

      {canRespond && !alreadyRejected && !countering && (
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={() => act('trade_accept', {})} style={{ flex: 1 }}>
            Accept
          </button>
          <button className="btn btn-secondary" onClick={() => act('trade_reject', {})} style={{ flex: 1 }}>
            Reject
          </button>
          <button className="btn btn-ghost" onClick={() => setCountering(true)}>
            Counter
          </button>
        </div>
      )}

      {countering && (
        <>
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div className="eyebrow" style={{ marginBottom: 6 }}>
                You give
              </div>
              <ResourceAmounts amounts={give} onChange={setGive} />
            </div>
            <div style={{ flex: 1 }}>
              <div className="eyebrow" style={{ marginBottom: 6 }}>
                You want
              </div>
              <ResourceAmounts amounts={want} onChange={setWant} />
            </div>
          </div>
          <button className="btn btn-secondary" onClick={submitCounter}>
            Send Counter
          </button>
        </>
      )}
    </div>
  )
}

function TradePanel({ game, myName, isCurrentPlayer, act }) {
  const otherPlayers = game.order.filter((n) => n !== myName)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div className="eyebrow">Trade</div>
      {isCurrentPlayer && <BankTrade bankRatios={game.legal?.bank_ratios} act={act} />}
      {game.trade ? (
        <ActiveTrade trade={game.trade} myName={myName} isCurrentPlayer={isCurrentPlayer} act={act} />
      ) : (
        isCurrentPlayer && <ProposeTrade otherPlayers={otherPlayers} act={act} />
      )}
    </div>
  )
}

export default TradePanel
