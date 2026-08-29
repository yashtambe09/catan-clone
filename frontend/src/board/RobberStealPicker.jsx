function RobberStealPicker({ players, onConfirm, onCancel }) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'oklch(20% 0.02 60 / 0.35)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 20,
      }}
    >
      <div className="card card-shadow" style={{ width: 320, padding: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <h2 style={{ fontSize: 18 }}>Move the robber</h2>
        <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted)' }}>
          Steal a resource from a player on this hex, or leave it be.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {players.map((name) => (
            <button key={name} className="btn btn-secondary" onClick={() => onConfirm(name)}>
              Steal from {name}
            </button>
          ))}
          <button className="btn btn-ghost" onClick={() => onConfirm(null)}>
            Steal from nobody
          </button>
        </div>
        <button className="btn btn-ghost" onClick={onCancel} style={{ alignSelf: 'center' }}>
          Cancel
        </button>
      </div>
    </div>
  )
}

export default RobberStealPicker
