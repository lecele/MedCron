const AnimatedLogo = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 130" style={{ width: '100%', maxWidth: '420px', height: 'auto' }}>
      <defs>
        <linearGradient id="textGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#a7d4c5" />
        </linearGradient>
        <linearGradient id="pillGlow" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="rgba(18,204,143,0.8)" />
          <stop offset="100%" stopColor="rgba(8,122,84,0.3)" />
        </linearGradient>
        <linearGradient id="glassBorder" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.7)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.1)" />
        </linearGradient>
        <style>{`
          @keyframes pulseLine {
            0% { stroke-dashoffset: 200; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { stroke-dashoffset: -200; opacity: 0; }
          }
          @keyframes floatPill {
            0% { transform: translateY(0) rotate(55deg); }
            50% { transform: translateY(-8px) rotate(55deg); }
            100% { transform: translateY(0) rotate(55deg); }
          }
          .ekg-line { stroke-dasharray: 200; animation: pulseLine 3s linear infinite; }
          .pill-group { animation: floatPill 4.5s ease-in-out infinite; transform-origin: 0 0; }
        `}</style>
      </defs>

      <g transform="translate(60, 65)">
        <g className="pill-group">
          <rect x="-35" y="-10" width="70" height="70" rx="35" fill="rgba(18,204,143,0.35)" filter="blur(16px)" />
          <rect x="-28" y="-60" width="56" height="120" rx="28" fill="rgba(255,255,255,0.06)" stroke="url(#glassBorder)" strokeWidth="2.5" />
          <path d="M-28,0 L28,0 L28,32 A 28 28 0 0 1 -28,32 Z" fill="url(#pillGlow)" />
          <g stroke="rgba(255,255,255,0.95)" strokeWidth="2.5" fill="none">
            <polyline points="-14,5 -14,-25" />
            <circle cx="-14" cy="-25" r="3.5" fill="#fff" />
            <polyline points="-2,5 -2,-12 8,-22 8,-42" />
            <circle cx="8" cy="-42" r="3.5" fill="#fff" />
            <polyline points="10,5 10,-8 18,-16 18,-30" />
            <circle cx="18" cy="-30" r="3.5" fill="#fff" />
          </g>
          <path d="M-22,-35 A 22 22 0 0 1 0,-57 L 4,-57 A 26 26 0 0 0 -18,-31 Z" fill="rgba(255,255,255,0.5)" />
          <path d="M-22,35 A 22 22 0 0 0 0,57 L 4,57 A 26 26 0 0 1 -18,31 Z" fill="rgba(255,255,255,0.2)" />
          <circle cx="-10" cy="20" r="1.5" fill="#fff" opacity="0.8" />
          <circle cx="5" cy="40" r="1" fill="#fff" opacity="0.6" />
          <circle cx="12" cy="15" r="2" fill="#fff" opacity="0.9" />
          <circle cx="-18" cy="45" r="1.5" fill="#fff" opacity="0.5" />
        </g>
      </g>

      <g transform="translate(140, 0)">
        <text x="0" y="72" fontSize="66" fontWeight="800" fill="url(#textGrad)" letterSpacing="-1.5">
          MedCron
        </text>
        <text x="140" y="105" fontSize="16.5" fontWeight="500" fill="#ffffff" letterSpacing="0.5" textAnchor="middle">
          Medicação na Hora Certa
        </text>
      </g>
    </svg>
  </div>
)

export default AnimatedLogo
