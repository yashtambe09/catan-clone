import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import AuthScreen from './AuthScreen'
import GameScreen from './board/GameScreen'
import Lobby from './lobby/Lobby'
import TopNav from './nav/TopNav'
import StatsPage from './stats/StatsPage'
import { connectWithToken, socket } from './socket'
import { setStatus } from './store/connectionSlice'
import { logout, setAuthError } from './store/authSlice'
import { leaveRoom, setError, setRoom } from './store/roomSlice'

function App() {
  const dispatch = useDispatch()
  const { token, username } = useSelector((state) => state.auth)
  const status = useSelector((state) => state.connection.status)
  const { room } = useSelector((state) => state.room)
  const [view, setView] = useState('play')

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

  function act(action, payload) {
    socket.emit('game_action', { action, payload }, (response) => {
      if (response.error) dispatch(setError(response.message))
    })
  }

  function handleLogout() {
    dispatch(leaveRoom())
    dispatch(logout())
  }

  if (room && room.phase === 'in_game' && room.game) {
    return <GameScreen room={room} myName={username} act={act} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <TopNav view={view} onSetView={setView} username={username} onLogout={handleLogout} />
      {status !== 'connected' && (
        <p style={{ textAlign: 'center', color: 'var(--color-muted)', margin: '8px 0 0' }}>
          socket status: {status}
        </p>
      )}
      {view === 'stats' ? <StatsPage /> : <Lobby username={username} />}
    </div>
  )
}

export default App
