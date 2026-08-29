import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import AuthScreen from './AuthScreen'
import GamePanel from './board/GamePanel'
import HexBoard from './board/HexBoard'
import { connectWithToken, socket } from './socket'
import { setStatus } from './store/connectionSlice'
import { logout, setAuthError } from './store/authSlice'
import { leaveRoom, setError, setRoom } from './store/roomSlice'

function App() {
  const dispatch = useDispatch()
  const { token, username } = useSelector((state) => state.auth)
  const status = useSelector((state) => state.connection.status)
  const { room, error } = useSelector((state) => state.room)

  const [createPlayerCount, setCreatePlayerCount] = useState(4)
  const [joinCode, setJoinCode] = useState('')

  useEffect(() => {
    if (!token) return undefined

    connectWithToken(token)

    socket.on('connect', () => dispatch(setStatus('connected')))
    socket.on('disconnect', () => dispatch(setStatus('disconnected')))
    socket.on('connect_error', (err) => {
      dispatch(setAuthError(err.message || 'could not connect - please log in again'))
      dispatch(logout())
    })
    socket.on('room_updated', (updatedRoom) => dispatch(setRoom(updatedRoom)))
    socket.on('game_started', (updatedRoom) => dispatch(setRoom(updatedRoom)))
    socket.on('game_updated', (updatedRoom) => dispatch(setRoom(updatedRoom)))

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('connect_error')
      socket.off('room_updated')
      socket.off('game_started')
      socket.off('game_updated')
      socket.disconnect()
    }
  }, [token, dispatch])

  useEffect(() => {
    if (status === 'disconnected' && room) {
      dispatch(setError('Disconnected — rejoin the room'))
      dispatch(leaveRoom())
    }
  }, [status, room, dispatch])

  if (!token) {
    return <AuthScreen />
  }

  function handleCreate(e) {
    e.preventDefault()
    socket.emit('create_room', { player_count: Number(createPlayerCount) }, (response) => {
      if (response.error) {
        dispatch(setError(response.message))
      } else {
        dispatch(setRoom(response.room))
      }
    })
  }

  function handleJoin(e) {
    e.preventDefault()
    socket.emit('join_room', { code: joinCode }, (response) => {
      if (response.error) {
        dispatch(setError(response.message))
      } else {
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

  function handleLogout() {
    dispatch(leaveRoom())
    dispatch(logout())
  }

  const me = room?.players.find((p) => p.name === username)

  return (
    <div>
      <h1>Catan Clone</h1>
      <p>
        Logged in as {username} — socket status: {status}{' '}
        <button onClick={handleLogout}>Log out</button>
      </p>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!room && (
        <div>
          <form onSubmit={handleCreate}>
            <h2>Create a room</h2>
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
                {!player.connected && ' [disconnected]'}
              </li>
            ))}
          </ul>
          {me?.is_host && <button onClick={handleStart}>Start Game</button>}
        </div>
      )}

      {room && room.phase === 'in_game' && (
        <div>
          <HexBoard board={room.board} />
          {room.game && <GamePanel room={room} myName={username} act={act} />}
        </div>
      )}
    </div>
  )
}

export default App
