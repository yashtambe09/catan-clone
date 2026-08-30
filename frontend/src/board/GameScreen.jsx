import { useState } from 'react'
import { useSelector } from 'react-redux'
import HexBoard from './HexBoard'
import DiceRoller from './DiceRoller'
import ResourceBar from './ResourceBar'
import DiscardModal from './DiscardModal'
import PlayerDashboard from '../player/PlayerDashboard'
import PlayerStrip from '../player/PlayerStrip'
import TurnIndicator from '../player/TurnIndicator'
import BuildPanel from '../panels/BuildPanel'
import TradePanel from '../panels/TradePanel'
import DevCardHand from '../panels/DevCardHand'
import MobileActionSheet from '../panels/MobileActionSheet'
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

  const devCardHandProps = {
    playingKnight,
    onStartKnight: () => setPlayingKnight(true),
    onCancelKnight: () => setPlayingKnight(false),
    playingRoadBuilding,
    onStartRoadBuilding: () => setPlayingRoadBuilding(true),
    onCancelRoadBuilding: () => setPlayingRoadBuilding(false),
  }

  return (
    <div className="game-screen">
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
      <div className="game-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
          <img src={logo} width={22} height={22} alt="" />
          <div>
            <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>
              CATAN
            </div>
            <div className="game-header-subtitle" style={{ fontSize: 12, color: 'var(--color-muted)', lineHeight: 1.2 }}>
              Room {room.code} · {room.max_players} players
            </div>
          </div>
        </div>

        <TurnIndicator
          key={`${game.current_player}-${game.phase}`}
          isMe={isMe}
          currentPlayerName={game.current_player}
          phase={game.phase}
        />

        <DiceRoller
          key={`${game.turn_number}-${game.last_roll ? game.last_roll.join(',') : 'none'}`}
          lastRoll={game.last_roll}
        />
      </div>

      <PlayerStrip game={game} myName={myName} />

      <div className="game-body">
        <PlayerDashboard game={game} myName={myName} />

        <div className="board-viewport-wrapper">
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

        <div className="desktop-action-panel">
          {isMe && game.phase === 'build' && (
            <>
              <BuildPanel me={me} devCardsRemaining={game.dev_cards_remaining} act={act} />
              <DevCardHand me={me} act={act} {...devCardHandProps} />
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

      <MobileActionSheet
        game={game}
        me={me}
        myName={myName}
        act={act}
        isMe={isMe}
        {...devCardHandProps}
      />

      {myDiscard && <DiscardModal required={myDiscard} onSubmit={(resources) => act('discard', { resources })} />}
    </div>
  )
}

export default GameScreen
