import { usePrevious } from '../hooks/usePrevious'
import woodCard from '../assets/resources/wood.svg'
import brickCard from '../assets/resources/brick.svg'
import sheepCard from '../assets/resources/sheep.svg'
import wheatCard from '../assets/resources/wheat.svg'
import oreCard from '../assets/resources/ore.svg'
import devCardBack from '../assets/dev-cards/card-back.svg'

const RESOURCES = ['wood', 'brick', 'sheep', 'wheat', 'ore']
const RESOURCE_CARD_ICONS = { wood: woodCard, brick: brickCard, sheep: sheepCard, wheat: wheatCard, ore: oreCard }
// Resource/dev-card art is a 120x168 card silhouette (5:7 ratio) - scaled down
// to a small chip icon here, same ratio preserved.
const CARD_ICON_WIDTH = 22
const CARD_ICON_HEIGHT = 31

function ResourceBar({ me, canRoll, act }) {
  const resources = me?.resources || {}
  const prevResources = usePrevious(resources) || {}
  const devCount = me?.dev_card_count ?? 0

  return (
    <div
      className="resource-bar"
      style={{
        borderTop: '1px solid var(--color-border-soft)',
        background: 'var(--color-surface)',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
        <span className="eyebrow">Your resources</span>
        <div className="resource-row" style={{ display: 'flex', gap: 10 }}>
          {RESOURCES.map((r) => {
            const value = resources[r] || 0
            const delta = value - (prevResources[r] ?? value)
            return (
              <div
                key={`${r}-${value}`}
                className={delta > 0 ? 'resource-flash' : ''}
                style={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 999,
                  background: 'var(--color-bg)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <img
                  src={RESOURCE_CARD_ICONS[r]}
                  alt={r}
                  width={CARD_ICON_WIDTH}
                  height={CARD_ICON_HEIGHT}
                  style={{ borderRadius: 3, flexShrink: 0 }}
                />
                <span style={{ fontWeight: 700, fontSize: 13 }}>{value}</span>
                {delta > 0 && (
                  <span
                    className="float-up-fade"
                    style={{
                      position: 'absolute',
                      top: -14,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      fontSize: 12,
                      fontWeight: 700,
                      color: 'var(--color-success)',
                    }}
                  >
                    +{delta}
                  </span>
                )}
              </div>
            )
          })}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              borderRadius: 999,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
            }}
          >
            <img
              src={devCardBack}
              alt="dev cards"
              width={CARD_ICON_WIDTH}
              height={CARD_ICON_HEIGHT}
              style={{ borderRadius: 3, flexShrink: 0 }}
            />
            <span style={{ fontWeight: 700, fontSize: 13 }}>{devCount} dev card{devCount === 1 ? '' : 's'}</span>
          </div>
        </div>
      </div>
      {canRoll && (
        <button
          className="btn"
          style={{ background: 'var(--resource-wheat)', color: 'var(--color-ink)', padding: '14px 32px' }}
          onClick={() => act('roll', {})}
        >
          Roll Dice
        </button>
      )}
    </div>
  )
}

export default ResourceBar
