const AlertModal = ({ alerts, onConfirm, onCancel }) => (
  <div style={{
    position: 'fixed', top: 0, left: 0,
    width: '100vw', height: '100vh',
    background: 'rgba(0,0,0,0.85)',
    backdropFilter: 'blur(5px)',
    zIndex: 9999,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '1rem'
  }}>
    <div className="glass-card animate-fade" style={{
      background: 'rgba(255, 30, 30, 0.15)',
      border: '1px solid rgba(255, 30, 30, 0.4)',
      padding: '2rem', borderRadius: '24px',
      maxWidth: '500px', width: '100%'
    }}>
      <h2 style={{ color: '#ff4d4d', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem', fontSize: '1.4rem' }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        Alerta Farmacológico
      </h2>
      <p style={{ color: 'white', marginBottom: '1.5rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
        O assistente detectou possíveis riscos na dosagem ao analisar os Limites de Bula com o seu peso:
      </p>
      <ul style={{ color: '#ffb3b3', marginBottom: '2rem', paddingLeft: '1.5rem', fontSize: '0.9rem', lineHeight: '1.6' }}>
        {alerts.map((a, i) => <li key={i} style={{ marginBottom: '10px' }}>{a}</li>)}
      </ul>
      <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
        <button
          className="action-btn"
          onClick={onConfirm}
          style={{ padding: '1rem', background: '#ff4d4d', color: 'white', border: 'none', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer', width: '100%' }}
        >
          Criar Alarme e Assumir Risco
        </button>
        <button
          className="action-btn"
          onClick={onCancel}
          style={{ padding: '0.8rem', background: 'transparent', color: 'white', border: '1px solid rgba(255,255,255,0.3)', borderRadius: '12px', cursor: 'pointer', width: '100%' }}
        >
          Cancelar Agendamento
        </button>
      </div>
    </div>
  </div>
)

export default AlertModal
