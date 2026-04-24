const PillIcon = ({ size = 22, color = 'var(--accent)' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ filter: 'drop-shadow(0 0 4px rgba(18,204,143,0.3))' }}
  >
    <path d="M10.5 20.5l-6-6a4.95 4.95 0 1 1 7-7l6 6a4.95 4.95 0 1 1-7 7Z" />
    <path d="M8.5 8.5l7 7" />
  </svg>
)

export default PillIcon
