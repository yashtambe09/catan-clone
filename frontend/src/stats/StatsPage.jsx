import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setStats, setStatsError, setStatsLoading } from '../store/statsSlice'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function StatCard({ label, value, color }) {
  return (
    <div className="card">
      <div className="eyebrow" style={{ marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontFamily: 'var(--font-heading)', fontSize: 30, fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  )
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function ordinal(n) {
  if (n == null) return '—'
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

function StatsPage() {
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.token)
  const username = useSelector((state) => state.auth.username)
  const { summary, matches, status, error } = useSelector((state) => state.stats)

  useEffect(() => {
    dispatch(setStatsLoading())
    fetch(`${BACKEND_URL}/stats/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'failed to load stats')
        dispatch(setStats(data))
      })
      .catch((err) => dispatch(setStatsError(err.message)))
  }, [dispatch, token])

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        overflow: 'auto',
        padding: '36px 56px',
        display: 'flex',
        flexDirection: 'column',
        gap: 28,
      }}
    >
      <div>
        <h1 style={{ fontSize: 26, marginBottom: 4 }}>Career Stats</h1>
        <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: 14 }}>
          {username} — settling since Day 1
        </p>
      </div>

      {status === 'loading' && <p style={{ color: 'var(--color-muted)' }}>Loading…</p>}
      {status === 'error' && <p style={{ color: 'var(--color-error)' }}>{error}</p>}

      {status === 'loaded' && summary && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 20 }}>
            <StatCard label="Games Played" value={summary.games_played} color="var(--color-ink)" />
            <StatCard label="Wins" value={summary.wins} color="var(--color-success)" />
            <StatCard label="Losses" value={summary.losses} color="var(--color-ink)" />
            <StatCard label="Win Rate" value={`${summary.win_rate}%`} color="var(--color-accent)" />
          </div>

          <div
            className="card"
            style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}
          >
            <div
              style={{
                padding: '16px 24px',
                borderBottom: '1px solid var(--color-border-soft)',
                fontWeight: 700,
                fontSize: 15,
              }}
            >
              Match History
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1.1fr 2fr 1fr 1fr 1fr',
                gap: 12,
                padding: '10px 24px',
              }}
              className="eyebrow"
            >
              <span>Date</span>
              <span>Opponents</span>
              <span>Board</span>
              <span>Placement</span>
              <span>Result</span>
            </div>
            {matches.length === 0 && (
              <p style={{ padding: '14px 24px', color: 'var(--color-muted)' }}>No games played yet.</p>
            )}
            {matches.map((m, i) => (
              <div
                key={i}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.1fr 2fr 1fr 1fr 1fr',
                  gap: 12,
                  padding: '14px 24px',
                  alignItems: 'center',
                  fontSize: 14,
                  borderTop: i > 0 ? '1px solid oklch(93% 0.01 80)' : 'none',
                }}
              >
                <span>{formatDate(m.started_at)}</span>
                <span>{m.opponents.join(', ') || '—'}</span>
                <span>{m.board_size}</span>
                <span>{ordinal(m.placement)}</span>
                <span
                  className={`badge ${m.result === 'win' ? 'badge-win' : 'badge-loss'}`}
                  style={{ justifySelf: 'start' }}
                >
                  {m.result === 'win' ? 'Win' : 'Loss'}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default StatsPage
