import { useState } from 'react'
import BuildPanel from './BuildPanel'
import TradePanel from './TradePanel'
import DevCardHand from './DevCardHand'

function MobileActionSheet({
  game,
  me,
  myName,
  act,
  isMe,
  playingKnight,
  onStartKnight,
  onCancelKnight,
  playingRoadBuilding,
  onStartRoadBuilding,
  onCancelRoadBuilding,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const showBuild = isMe && game.phase === 'build'
  const showTrade = game.phase === 'build' && (isMe || game.trade)

  if (!showBuild && !showTrade) return null

  return (
    <div className="mobile-action-sheet">
      <button className="mobile-action-sheet-handle" onClick={() => setIsOpen((v) => !v)}>
        Build &amp; Trade {isOpen ? '▼' : '▲'}
      </button>
      <div className={`mobile-action-sheet-body${isOpen ? ' is-open' : ''}`}>
        {showBuild && (
          <>
            <BuildPanel me={me} devCardsRemaining={game.dev_cards_remaining} act={act} />
            <DevCardHand
              me={me}
              act={act}
              playingKnight={playingKnight}
              onStartKnight={onStartKnight}
              onCancelKnight={onCancelKnight}
              playingRoadBuilding={playingRoadBuilding}
              onStartRoadBuilding={onStartRoadBuilding}
              onCancelRoadBuilding={onCancelRoadBuilding}
            />
          </>
        )}
        {showTrade && <TradePanel game={game} myName={myName} isCurrentPlayer={isMe} act={act} />}
        {showBuild && (
          <button className="btn btn-primary btn-block" onClick={() => act('end_turn', {})}>
            End Turn
          </button>
        )}
      </div>
    </div>
  )
}

export default MobileActionSheet
