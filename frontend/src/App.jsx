import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import HexBoard from './board/HexBoard'
import { socket } from './socket'
import { setStatus } from './store/connectionSlice'

function App() {
  const dispatch = useDispatch()
  const status = useSelector((state) => state.connection.status)
  const [playerCount, setPlayerCount] = useState(4)

  useEffect(() => {
    socket.connect()

    socket.on('connect', () => dispatch(setStatus('connected')))
    socket.on('disconnect', () => dispatch(setStatus('disconnected')))

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.disconnect()
    }
  }, [dispatch])

  return (
    <div>
      <h1>Catan Clone</h1>
      <p>Socket status: {status}</p>

      <div>
        {[2, 3, 4, 5, 6].map((count) => (
          <button key={count} onClick={() => setPlayerCount(count)} disabled={count === playerCount}>
            {count} players
          </button>
        ))}
      </div>

      <HexBoard playerCount={playerCount} />
    </div>
  )
}

export default App
