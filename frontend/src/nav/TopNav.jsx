function Logo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M12 2 L21 7.5 V16.5 L12 22 L3 16.5 V7.5 Z" fill="var(--color-accent)" />
      <path d="M12 2 L21 7.5 L12 12 L3 7.5 Z" fill="var(--resource-wheat)" />
    </svg>
  )
}

function Tab({ label, active, onClick }) {
  return (
    <span
      onClick={onClick}
      style={{
        fontSize: 15,
        fontWeight: active ? 600 : 400,
        color: active ? 'var(--color-ink)' : 'var(--color-muted)',
        borderBottom: active ? '2px solid var(--color-accent)' : '2px solid transparent',
        paddingBottom: 4,
        cursor: 'pointer',
      }}
    >
      {label}
    </span>
  )
}

function TopNav({ view, onSetView, username, onLogout }) {
  const initial = username ? username[0].toUpperCase() : '?'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '26px 56px',
        borderBottom: '1px solid var(--color-border-soft)',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Logo />
        <span
          style={{
            fontFamily: 'var(--font-heading)',
            fontWeight: 700,
            fontSize: 21,
            letterSpacing: '0.02em',
            color: 'var(--color-ink)',
          }}
        >
          CATAN
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
        <Tab label="Play" active={view === 'play'} onClick={() => onSetView('play')} />
        <Tab label="Stats" active={view === 'stats'} onClick={() => onSetView('stats')} />
        <div className="avatar" title={username} style={{ background: 'var(--color-accent)' }}>
          {initial}
        </div>
        <button className="btn btn-ghost" onClick={onLogout} style={{ padding: '6px 10px' }}>
          Log out
        </button>
      </div>
    </div>
  )
}

export default TopNav
