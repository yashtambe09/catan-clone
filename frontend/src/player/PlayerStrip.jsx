import PlayerRow from './PlayerRow'

function PlayerStrip({ game, myName }) {
  return (
    <div className="player-strip">
      {game.order.map((name, i) => (
        <PlayerRow
          key={name}
          player={game.players[name]}
          seatIndex={i}
          isViewer={name === myName}
          isCurrentTurn={name === game.current_player}
          hasLongestRoad={game.longest_road_holder === name}
          hasLargestArmy={game.largest_army_holder === name}
          compact
        />
      ))}
    </div>
  )
}

export default PlayerStrip
