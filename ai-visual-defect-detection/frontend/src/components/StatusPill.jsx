function toneClasses(tone) {
  switch (tone) {
    case 'good':
      return 'bg-accent-500/10 text-accent-300 border-accent-500/30'
    case 'bad':
      return 'bg-signal-red/10 text-signal-red border-signal-red/30'
    case 'pending':
    default:
      return 'bg-ink-500/10 text-ink-500 border-ink-500/25'
  }
}

function dotClasses(tone) {
  switch (tone) {
    case 'good':
      return 'bg-accent-400'
    case 'bad':
      return 'bg-signal-red'
    default:
      return 'bg-ink-500'
  }
}

export default function StatusPill({ tone = 'pending', label, animated = false }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider ${toneClasses(
        tone,
      )}`}
    >
      <span className="relative flex h-1.5 w-1.5">
        {animated && (
          <span className={`absolute inline-flex h-full w-full animate-pulseRing rounded-full ${dotClasses(tone)}`} />
        )}
        <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${dotClasses(tone)} ${animated ? 'animate-pulseDot' : ''}`} />
      </span>
      {label}
    </span>
  )
}
