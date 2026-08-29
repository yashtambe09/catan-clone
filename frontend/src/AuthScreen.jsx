import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setAuthError, setCredentials } from './store/authSlice'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function Logo({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M12 2 L21 7.5 V16.5 L12 22 L3 16.5 V7.5 Z" fill="var(--color-accent)" />
      <path d="M12 2 L21 7.5 L12 12 L3 7.5 Z" fill="var(--resource-wheat)" />
    </svg>
  )
}

function BackgroundHexes() {
  return (
    <>
      <svg
        width="360"
        height="416"
        viewBox="0 0 90 104"
        style={{ position: 'absolute', left: -60, top: -40, opacity: 0.5 }}
      >
        <path
          d="M45 2 L88 27 V77 L45 102 L2 77 V27 Z"
          fill="none"
          stroke="var(--color-border)"
          strokeWidth="2"
        />
      </svg>
      <svg
        width="300"
        height="346"
        viewBox="0 0 90 104"
        style={{ position: 'absolute', right: -50, bottom: -50, opacity: 0.5 }}
      >
        <path
          d="M45 2 L88 27 V77 L45 102 L2 77 V27 Z"
          fill="none"
          stroke="var(--color-border)"
          strokeWidth="2"
        />
      </svg>
    </>
  )
}

function AuthScreen() {
  const dispatch = useDispatch()
  const error = useSelector((state) => state.auth.error)
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const isSignup = mode === 'signup'
  const passwordsMismatch = isSignup && confirmPassword.length > 0 && password !== confirmPassword

  function switchMode(next) {
    setMode(next)
    setConfirmPassword('')
    dispatch(setAuthError(null))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (passwordsMismatch) return

    setLoading(true)
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
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        width: '100%',
        minHeight: '100vh',
        background: 'var(--color-bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <BackgroundHexes />

      <form
        onSubmit={handleSubmit}
        className="card card-shadow"
        style={{
          width: 420,
          padding: 40,
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <Logo />
          <span
            style={{
              fontFamily: 'var(--font-heading)',
              fontWeight: 700,
              fontSize: 22,
              letterSpacing: '0.02em',
              color: 'var(--color-ink)',
            }}
          >
            CATAN
          </span>
        </div>

        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: 20, marginBottom: 6 }}>
            {isSignup ? 'Create your account' : 'Welcome back'}
          </h1>
          <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: 14 }}>
            {isSignup
              ? "Pick a username — you'll use it to challenge friends."
              : "Log in to join your friends' game."}
          </p>
        </div>

        {error && (
          <p
            style={{
              margin: 0,
              padding: '10px 14px',
              borderRadius: 8,
              background: 'var(--color-loss-bg)',
              color: 'var(--color-error)',
              fontSize: 14,
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            {error}
          </p>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="field">
            <span className="field-label">Username</span>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={isSignup ? 'e.g. settler_yash' : ''}
              autoComplete="username"
            />
          </div>
          <div className="field">
            <span className="field-label">Password</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isSignup ? 'At least 8 characters' : ''}
              autoComplete={isSignup ? 'new-password' : 'current-password'}
            />
          </div>
          {isSignup && (
            <div className="field">
              <span className="field-label">Confirm Password</span>
              <input
                className={`input${passwordsMismatch ? ' is-error' : ''}`}
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
              {passwordsMismatch && <span className="field-error">Passwords don't match</span>}
            </div>
          )}
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={loading || passwordsMismatch}>
          {loading ? (isSignup ? 'Signing up…' : 'Logging in…') : isSignup ? 'Sign Up' : 'Log In'}
        </button>

        <p style={{ textAlign: 'center', margin: 0, fontSize: 14, color: 'var(--color-muted)' }}>
          {isSignup ? (
            <>
              Already have an account?{' '}
              <a href="#" onClick={(e) => (e.preventDefault(), switchMode('login'))}>
                Log in
              </a>
            </>
          ) : (
            <>
              Don't have an account?{' '}
              <a href="#" onClick={(e) => (e.preventDefault(), switchMode('signup'))}>
                Sign up
              </a>
            </>
          )}
        </p>
      </form>
    </div>
  )
}

export default AuthScreen
