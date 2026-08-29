import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setAuthError, setCredentials } from './store/authSlice'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function AuthScreen() {
  const dispatch = useDispatch()
  const error = useSelector((state) => state.auth.error)
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      const res = await fetch(`${BACKEND_URL}/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        dispatch(setAuthError(data.detail || 'authentication failed'))
        return
      }
      dispatch(
        setCredentials({ token: data.access_token, username: data.username, userId: data.user_id }),
      )
    } catch {
      dispatch(setAuthError('could not reach the server'))
    }
  }

  return (
    <div>
      <h1>Catan Clone</h1>
      <div>
        <button type="button" onClick={() => setMode('login')} disabled={mode === 'login'}>
          Log In
        </button>
        <button type="button" onClick={() => setMode('signup')} disabled={mode === 'signup'}>
          Sign Up
        </button>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <button type="submit">{mode === 'login' ? 'Log In' : 'Sign Up'}</button>
      </form>
    </div>
  )
}

export default AuthScreen
