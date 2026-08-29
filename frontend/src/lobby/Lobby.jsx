import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { socket } from '../socket'
import { setError, setRoom } from '../store/roomSlice'

const PLAYER_COUNTS = [2, 3, 4, 5, 6]

function CreateRoomCard() {
  const dispatch = useDispatch()
  const [playerCount, setPlayerCount] = useState(4)

  function handleCreate(e) {
    e.preventDefault()
    socket.emit('create_room', { player_count: Number(playerCount) }, (response) => {
      if (response.error) {
        dispatch(setError(response.message))
      } else {
        dispatch(setRoom(response.room))
      }
    })
  }

  return (
    <form
      onSubmit={handleCreate}
      className="card card-shadow"
      style={{ width: 420, padding: 32, display: 'flex', flexDirection: 'column', gap: 20 }}
    >
      <div>
        <h2 style={{ fontSize: 22, marginBottom: 6 }}>Create a Game</h2>
        <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: 14, lineHeight: 1.5 }}>
          Pick a player count and open a new room.
        </p>
      </div>
      <div>
        <div className="eyebrow" style={{ marginBottom: 10 }}>
          Players
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {PLAYER_COUNTS.map((n) => (
            <button
              key={n}
              type="button"
              className={`chip${playerCount === n ? ' is-selected' : ''}`}
              onClick={() => setPlayerCount(n)}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
      <button type="submit" className="btn btn-primary btn-block">
        Create Room
      </button>
    </form>
  )
}

function JoinRoomCard() {
  const dispatch = useDispatch()
  const [joinCode, setJoinCode] = useState('')

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

  return (
    <form
      onSubmit={handleJoin}
      className="card card-shadow"
      style={{ width: 420, padding: 32, display: 'flex', flexDirection: 'column', gap: 20 }}
    >
      <div>
        <h2 style={{ fontSize: 22, marginBottom: 6 }}>Join a Game</h2>
        <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: 14, lineHeight: 1.5 }}>
          Enter the room code a friend sent you.
        </p>
      </div>
      <input
        className="input"
        value={joinCode}
        onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
        placeholder="e.g. F3XQ2R"
        style={{ fontSize: 16, letterSpacing: '0.12em', fontWeight: 700, textAlign: 'center' }}
      />
      <button type="submit" className="btn btn-secondary btn-block">
        Join Room
      </button>
    </form>
  )
}

function WaitingRoom({ room, username }) {
  const dispatch = useDispatch()
  const me = room.players.find((p) => p.name === username)

  function handleStart() {
    socket.emit('start_game', {}, (response) => {
      if (response.error) dispatch(setError(response.message))
    })
  }

  return (
    <div
      className="card card-shadow"
      style={{ width: 420, padding: 32, display: 'flex', flexDirection: 'column', gap: 20 }}
    >
      <div>
        <h2 style={{ fontSize: 22, marginBottom: 6 }}>Room {room.code}</h2>
        <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: 14 }}>
          {room.players.length} / {room.max_players} players
        </p>
      </div>
      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {room.players.map((player) => (
          <li
            key={player.name}
            style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'var(--color-ink)' }}
          >
            <span
              className="avatar avatar-sm"
              style={{ background: 'var(--color-accent)' }}
            >
              {player.name[0].toUpperCase()}
            </span>
            {player.name}
            {player.is_host && <span className="eyebrow">host</span>}
            {!player.connected && <span style={{ color: 'var(--color-muted)' }}>[disconnected]</span>}
          </li>
        ))}
      </ul>
      {me?.is_host && (
        <button className="btn btn-primary btn-block" onClick={handleStart}>
          Start Game
        </button>
      )}
    </div>
  )
}

function Lobby({ username }) {
  const { room, error } = useSelector((state) => state.room)

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 36,
        padding: '0 56px',
        flexWrap: 'wrap',
      }}
    >
      {error && (
        <p style={{ width: '100%', textAlign: 'center', color: 'var(--color-error)', fontWeight: 600 }}>
          {error}
        </p>
      )}
      {room ? (
        <WaitingRoom room={room} username={username} />
      ) : (
        <>
          <CreateRoomCard />
          <JoinRoomCard />
        </>
      )}
    </div>
  )
}

export default Lobby
