import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { socket } from './socket'
import { setStatus } from './store/connectionSlice'

function App() {
  const dispatch = useDispatch()
  const status = useSelector((state) => state.connection.status)

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
    </div>
  )
}

export default App
