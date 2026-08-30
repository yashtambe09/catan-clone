import { useState } from 'react'

const RESOURCES = ['wood', 'brick', 'sheep', 'wheat', 'ore']

function DiscardModal({ required, onSubmit }) {
  const [amounts, setAmounts] = useState({})

  const total = RESOURCES.reduce((sum, r) => sum + Number(amounts[r] || 0), 0)

  function submit() {
    onSubmit(Object.fromEntries(RESOURCES.map((r) => [r, Number(amounts[r] || 0)])))
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'oklch(20% 0.02 60 / 0.35)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 20,
      }}
    >
      <div
        className="card card-shadow"
        style={{ width: 340, maxWidth: '90vw', boxSizing: 'border-box', padding: 24, display: 'flex', flexDirection: 'column', gap: 14 }}
      >
        <h2 style={{ fontSize: 18 }}>Discard {required} cards</h2>
        <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted)' }}>
          A 7 was rolled — you have more than 7 cards.
        </p>
        {RESOURCES.map((r) => (
          <div key={r} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <span
              style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, textTransform: 'capitalize' }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
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
              style={{ width: 70 }}
              value={amounts[r] || ''}
              onChange={(e) => setAmounts({ ...amounts, [r]: e.target.value })}
            />
          </div>
        ))}
        <p style={{ margin: 0, fontSize: 13, color: total === required ? 'var(--color-success)' : 'var(--color-error)' }}>
          {total} / {required} selected
        </p>
        <button className="btn btn-primary btn-block" disabled={total !== required} onClick={submit}>
          Discard
        </button>
      </div>
    </div>
  )
}

export default DiscardModal
