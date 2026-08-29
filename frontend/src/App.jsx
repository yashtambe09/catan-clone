import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import GamePanel from './board/GamePanel'
import HexBoard from './board/HexBoard'
import { socket } from './socket'
import { setStatus } from './store/connectionSlice'
import { leaveRoom, setError, setMyName, setRoom } from './store/roomSlice'

function App() {
  const dispatch = useDispatch()
  const status = useSelector((state) => state.connection.status)
  const { myName, room, error } = useSelector((state) => state.room)

  const [createName, setCreateName] = useState('')
  const [createPlayerCount, setCreatePlayerCount] = useState(4)
  const [joinName, setJoinName] = useState('')
  const [joinCode, setJoinCode] = useState('')

  useEffect(() => {
    socket.connect()

    socket.on('connect', () => dispatch(setStatus('connected')))
    socket.on('disconnect', () => dispatch(setStatus('disconnected')))
    socket.on('room_updated', (updatedRoom) => dispatch(setRoom(updatedRoom)))
    socket.on('game_started', (updatedRoom) => dispatch(setRoom(updatedRoom)))
    socket.on('game_updated', (updatedRoom) => dispatch(setRoom(updatedRoom)))

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('room_updated')
      socket.off('game_started')
      socket.off('game_updated')
      socket.disconnect()
    }
  }, [dispatch])

  useEffect(() => {
    if (status === 'disconnected' && room) {
      dispatch(setError('Disconnected — rejoin with a new name'))
      dispatch(leaveRoom())
    }
  }, [status, room, dispatch])

  function handleCreate(e) {
    e.preventDefault()
    socket.emit(
      'create_room',
      { name: createName, player_count: Number(createPlayerCount) },
      (response) => {
        if (response.error) {
          dispatch(setError(response.message))
        } else {
          dispatch(setMyName(createName.trim()))
          dispatch(setRoom(response.room))
        }
      },
    )
  }

  function handleJoin(e) {
    e.preventDefault()
    socket.emit('join_room', { name: joinName, code: joinCode }, (response) => {
      if (response.error) {
        dispatch(setError(response.message))
      } else {
        dispatch(setMyName(joinName.trim()))
        dispatch(setRoom(response.room))
      }
    })
  }

  function handleStart() {
    socket.emit('start_game', {}, (response) => {
      if (response.error) dispatch(setError(response.message))
    })
  }

  function act(action, payload) {
    socket.emit('game_action', { action, payload }, (response) => {
      if (response.error) dispatch(setError(response.message))
    })
  }

  const me = room?.players.find((p) => p.name === myName)

  return (
    <div>
      <h1>Catan Clone</h1>
      <p>Socket status: {status}</p>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!room && (
        <div>
          <form onSubmit={handleCreate}>
            <h2>Create a room</h2>
            <input
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="Your name"
            />
            <select
              value={createPlayerCount}
              onChange={(e) => setCreatePlayerCount(e.target.value)}
            >
              {[2, 3, 4, 5, 6].map((n) => (
                <option key={n} value={n}>
                  {n} players
                </option>
              ))}
            </select>
            <button type="submit">Create Room</button>
          </form>

          <form onSubmit={handleJoin}>
            <h2>Join a room</h2>
            <input
              value={joinName}
              onChange={(e) => setJoinName(e.target.value)}
              placeholder="Your name"
            />
            <input
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="Room code"
            />
            <button type="submit">Join Room</button>
          </form>
        </div>
      )}

      {room && room.phase === 'lobby' && (
        <div>
          <h2>Room {room.code}</h2>
          <p>
            {room.players.length} / {room.max_players} players
          </p>
          <ul>
            {room.players.map((player) => (
              <li key={player.name}>
                {player.name} {player.is_host && '(host)'}
              </li>
            ))}
          </ul>
          {me?.is_host && <button onClick={handleStart}>Start Game</button>}
        </div>
      )}

      {room && room.phase === 'in_game' && (
        <div>
          <HexBoard board={room.board} />
          {room.game && <GamePanel room={room} myName={myName} act={act} />}
        </div>
      )}
    </div>
  )
}

export default App
