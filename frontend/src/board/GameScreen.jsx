import { useState } from 'react'
import { useSelector } from 'react-redux'
import HexBoard from './HexBoard'
import DiceRoller from './DiceRoller'
import ResourceBar from './ResourceBar'
import DiscardModal from './DiscardModal'
import PlayerDashboard from '../player/PlayerDashboard'
import TurnIndicator from '../player/TurnIndicator'
import BuildPanel from '../panels/BuildPanel'
import TradePanel from '../panels/TradePanel'
import DevCardHand from '../panels/DevCardHand'
import logo from '../assets/icons/logo.svg'

function GameScreen({ room, myName, act }) {
  const [playingKnight, setPlayingKnight] = useState(false)
  const [playingRoadBuilding, setPlayingRoadBuilding] = useState(false)
  const error = useSelector((state) => state.room.error)

  const game = room.game
  const me = game.players[myName]
  const isMe = game.current_player === myName
  const myDiscard = game.pending_discards[myName]

  function handleAct(action, payload) {
    if (action === 'play_knight') setPlayingKnight(false)
    act(action, payload)
  }

  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
      {error && (
        <div
          style={{
            position: 'absolute',
            top: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 30,
            padding: '10px 20px',
            borderRadius: 8,
            background: 'var(--color-error)',
            color: 'var(--color-on-accent)',
            fontWeight: 600,
            fontSize: 14,
            boxShadow: 'var(--shadow-card)',
          }}
        >
          {error}
        </div>
      )}
      <div
        style={{
          flexShrink: 0,
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
          borderBottom: '1px solid var(--color-border-soft)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img src={logo} width={22} height={22} alt="" />
          <div>
            <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>
              CATAN
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-muted)', lineHeight: 1.2 }}>
              Room {room.code} · {room.max_players} players
            </div>
          </div>
        </div>

        <TurnIndicator isMe={isMe} currentPlayerName={game.current_player} phase={game.phase} />

        <DiceRoller lastRoll={game.last_roll} turnNumber={game.turn_number} />
      </div>

      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <PlayerDashboard game={game} myName={myName} />

        <div
          style={{
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 20,
            boxSizing: 'border-box',
          }}
        >
          <HexBoard
            board={room.board}
            game={game}
            myName={myName}
            act={handleAct}
            playingKnight={playingKnight}
            playingRoadBuilding={playingRoadBuilding}
            onRoadBuildingDone={() => setPlayingRoadBuilding(false)}
          />
        </div>

        <div
          style={{
            width: 300,
            flexShrink: 0,
            boxSizing: 'border-box',
            padding: 20,
            borderLeft: '1px solid var(--color-border-soft)',
            background: 'oklch(95% 0.015 85)',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            overflowY: 'auto',
          }}
        >
          {isMe && game.phase === 'build' && (
            <>
              <BuildPanel me={me} devCardsRemaining={game.dev_cards_remaining} act={act} />
              <DevCardHand
                me={me}
                act={act}
                playingKnight={playingKnight}
                onStartKnight={() => setPlayingKnight(true)}
                onCancelKnight={() => setPlayingKnight(false)}
                playingRoadBuilding={playingRoadBuilding}
                onStartRoadBuilding={() => setPlayingRoadBuilding(true)}
                onCancelRoadBuilding={() => setPlayingRoadBuilding(false)}
              />
            </>
          )}

          {game.phase === 'build' && (isMe || game.trade) && (
            <TradePanel game={game} myName={myName} isCurrentPlayer={isMe} act={act} />
          )}

          <div style={{ flex: 1 }} />

          {isMe && game.phase === 'build' && (
            <button className="btn btn-primary btn-block" onClick={() => act('end_turn', {})}>
              End Turn
            </button>
          )}
        </div>
      </div>

      <ResourceBar me={me} canRoll={isMe && game.phase === 'roll'} act={act} />

      {myDiscard && <DiscardModal required={myDiscard} onSubmit={(resources) => act('discard', { resources })} />}
    </div>
  )
}

export default GameScreen
