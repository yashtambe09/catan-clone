import { COSTS, canAfford } from '../game/costs'

const MAX_SETTLEMENTS = 5
const MAX_CITIES = 4
const MAX_ROADS = 15

function CostDots({ cost }) {
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {Object.entries(cost).map(([resource, count]) => (
        <span
          key={resource}
          style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--color-muted)' }}
        >
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: '50%',
              background: `var(--resource-${resource})`,
              display: 'inline-block',
            }}
          />
          {count}
        </span>
      ))}
    </div>
  )
}

function BuildRow({ label, cost, affordable, piecesLeft }) {
  return (
    <div
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        padding: 12,
        opacity: affordable ? 1 : 0.45,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontWeight: 700, fontSize: 14 }}>{label}</span>
        {piecesLeft !== undefined && (
          <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>{piecesLeft} left</span>
        )}
      </div>
      <CostDots cost={cost} />
    </div>
  )
}

function BuildPanel({ me, devCardsRemaining, act }) {
  const resources = me?.resources || {}
  const settlementsLeft = MAX_SETTLEMENTS - (me?.settlements?.length || 0) - (me?.cities?.length || 0)
  const citiesLeft = MAX_CITIES - (me?.cities?.length || 0)
  const roadsLeft = MAX_ROADS - (me?.roads?.length || 0)
  const canBuyDevCard = canAfford(resources, COSTS.dev_card) && devCardsRemaining > 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div className="eyebrow" style={{ marginBottom: 4 }}>
        Build
      </div>
      <BuildRow label="Road" cost={COSTS.road} affordable={canAfford(resources, COSTS.road)} piecesLeft={roadsLeft} />
      <BuildRow
        label="Settlement"
        cost={COSTS.settlement}
        affordable={canAfford(resources, COSTS.settlement)}
        piecesLeft={settlementsLeft}
      />
      <BuildRow label="City" cost={COSTS.city} affordable={canAfford(resources, COSTS.city)} piecesLeft={citiesLeft} />
      <div
        className="card"
        style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: 12, opacity: canBuyDevCard ? 1 : 0.45 }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ fontWeight: 700, fontSize: 14 }}>Dev Card</span>
          <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>{devCardsRemaining} left</span>
        </div>
        <CostDots cost={COSTS.dev_card} />
        <button
          className="btn btn-secondary"
          disabled={!canBuyDevCard}
          onClick={() => act('buy_dev_card', {})}
          style={{ marginTop: 4 }}
        >
          Buy
        </button>
      </div>
    </div>
  )
}

export default BuildPanel
