import { useState } from 'react'

const RESOURCES = ['wood', 'brick', 'sheep', 'wheat', 'ore']

const CARD_LABELS = {
  knight: 'Knight',
  victory_point: 'Victory Point',
  monopoly: 'Monopoly',
  road_building: 'Road Building',
  year_of_plenty: 'Year of Plenty',
}

function MonopolyPicker({ onSubmit, onCancel }) {
  const [resource, setResource] = useState(RESOURCES[0])
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
      <select className="input" value={resource} onChange={(e) => setResource(e.target.value)}>
        {RESOURCES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <button className="btn btn-secondary" onClick={() => onSubmit(resource)}>
        Take all
      </button>
      <button className="btn btn-ghost" onClick={onCancel}>
        Cancel
      </button>
    </div>
  )
}

function YearOfPlentyPicker({ onSubmit, onCancel }) {
  const [first, setFirst] = useState(RESOURCES[0])
  const [second, setSecond] = useState(RESOURCES[0])
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      <select className="input" value={first} onChange={(e) => setFirst(e.target.value)}>
        {RESOURCES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <select className="input" value={second} onChange={(e) => setSecond(e.target.value)}>
        {RESOURCES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <button className="btn btn-secondary" onClick={() => onSubmit([first, second])}>
        Take
      </button>
      <button className="btn btn-ghost" onClick={onCancel}>
        Cancel
      </button>
    </div>
  )
}

function DevCardHand({
  me,
  act,
  playingKnight,
  onStartKnight,
  onCancelKnight,
  playingRoadBuilding,
  onStartRoadBuilding,
  onCancelRoadBuilding,
}) {
  const [picking, setPicking] = useState(null)

  const dev = me?.dev_cards || {}
  const devNew = me?.dev_new || {}
  const hasAny = Object.values(dev).some((n) => n > 0) || Object.values(devNew).some((n) => n > 0)

  if (!hasAny) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div className="eyebrow">Dev Cards</div>
      {Object.entries(dev)
        .filter(([, count]) => count > 0)
        .map(([card, count]) => (
          <div key={card} className="card" style={{ padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 700, fontSize: 13 }}>{CARD_LABELS[card]}</span>
              <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>x{count}</span>
            </div>
            {card === 'knight' &&
              (playingKnight ? (
                <button className="btn btn-ghost" onClick={onCancelKnight}>
                  Cancel (pick a hex on the board)
                </button>
              ) : (
                <button className="btn btn-secondary" onClick={onStartKnight}>
                  Play
                </button>
              ))}
            {card === 'road_building' &&
              (playingRoadBuilding ? (
                <button className="btn btn-ghost" onClick={onCancelRoadBuilding}>
                  Cancel (pick 2 roads on the board)
                </button>
              ) : (
                <button className="btn btn-secondary" onClick={onStartRoadBuilding}>
                  Play
                </button>
              ))}
            {card === 'monopoly' &&
              (picking === 'monopoly' ? (
                <MonopolyPicker
                  onSubmit={(resource) => {
                    act('play_monopoly', { resource })
                    setPicking(null)
                  }}
                  onCancel={() => setPicking(null)}
                />
              ) : (
                <button className="btn btn-secondary" onClick={() => setPicking('monopoly')}>
                  Play
                </button>
              ))}
            {card === 'year_of_plenty' &&
              (picking === 'year_of_plenty' ? (
                <YearOfPlentyPicker
                  onSubmit={(resources) => {
                    act('play_year_of_plenty', { resources })
                    setPicking(null)
                  }}
                  onCancel={() => setPicking(null)}
                />
              ) : (
                <button className="btn btn-secondary" onClick={() => setPicking('year_of_plenty')}>
                  Play
                </button>
              ))}
            {card === 'victory_point' && (
              <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>Counts toward your score</span>
            )}
          </div>
        ))}
      {Object.entries(devNew)
        .filter(([, count]) => count > 0)
        .map(([card, count]) => (
          <div key={`new-${card}`} style={{ fontSize: 12, color: 'var(--color-muted)', padding: '0 4px' }}>
            {CARD_LABELS[card]} x{count} (bought this turn — playable next turn)
          </div>
        ))}
    </div>
  )
}

export default DevCardHand
