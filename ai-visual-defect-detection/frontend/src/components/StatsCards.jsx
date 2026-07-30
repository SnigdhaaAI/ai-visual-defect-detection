import { useEffect, useRef, useState } from 'react'
import { ClipboardList, CheckCircle2, AlertTriangle, Target } from 'lucide-react'

function useCountUp(value, duration = 600) {
  const [display, setDisplay] = useState(0)
  const frameRef = useRef(null)
  const startRef = useRef(null)
  const fromRef = useRef(0)

  useEffect(() => {
    const target = Number.isFinite(value) ? value : 0
    fromRef.current = display
    startRef.current = null

    function step(ts) {
      if (startRef.current === null) startRef.current = ts
      const elapsed = ts - startRef.current
      const progress = Math.min(1, elapsed / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = fromRef.current + (target - fromRef.current) * eased
      setDisplay(current)
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step)
      } else {
        setDisplay(target)
      }
    }

    frameRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frameRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, duration])

  return display
}

function StatCard({ icon: Icon, label, value, description, accent, isNumeric, index }) {
  const animated = useCountUp(isNumeric ? value : 0)
  const displayValue = isNumeric ? Math.round(animated).toLocaleString() : value

  return (
    <div
      style={{ animationDelay: `${index * 60}ms` }}
      className="animate-rise group relative overflow-hidden rounded-xl border border-base-600 bg-base-900/70 p-5 shadow-panel transition-all duration-300 ease-out hover:-translate-y-0.5 hover:border-base-500 hover:bg-base-900 hover:shadow-panelHover"
    >
      <div className="pointer-events-none absolute inset-0 bg-blueprint bg-gridFine opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div
        className={`absolute -right-8 -top-8 h-28 w-28 rounded-full opacity-[0.08] blur-2xl transition-opacity duration-300 group-hover:opacity-[0.15] ${accent.glow}`}
      />
      <div className="relative flex items-start justify-between">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg border ${accent.iconWrap}`}>
          <Icon className={`h-5 w-5 ${accent.icon}`} strokeWidth={1.75} />
        </div>
        <span className={`h-1.5 w-1.5 rounded-full ${accent.glow} opacity-60`} />
      </div>
      <p className="relative mt-4 font-mono text-[28px] font-semibold leading-none tabular text-ink-100">
        {displayValue}
      </p>
      <p className="relative mt-2 text-sm font-medium text-ink-300">{label}</p>
      <p className="relative mt-0.5 text-xs text-ink-600">{description}</p>
    </div>
  )
}

export default function StatsCards({ total, good, defective }) {
  const cards = [
    {
      icon: ClipboardList,
      label: 'Total Inspections',
      value: total,
      isNumeric: true,
      description: 'All records logged to date',
      accent: { icon: 'text-accent-400', iconWrap: 'border-accent-500/25 bg-accent-500/10', glow: 'bg-accent-400' },
    },
    {
      icon: CheckCircle2,
      label: 'Good Products',
      value: good,
      isNumeric: true,
      description: 'Passed automated inspection',
      accent: { icon: 'text-accent-300', iconWrap: 'border-accent-400/25 bg-accent-400/10', glow: 'bg-accent-300' },
    },
    {
      icon: AlertTriangle,
      label: 'Defective Products',
      value: defective,
      isNumeric: true,
      description: 'Flagged for quality review',
      accent: { icon: 'text-signal-red', iconWrap: 'border-signal-red/25 bg-signal-red/10', glow: 'bg-signal-red' },
    },
    {
      icon: Target,
      label: 'Model Test F1 Score',
      value: '99.44%',
      isNumeric: false,
      description: 'ResNet18 validation benchmark',
      accent: { icon: 'text-amber-400', iconWrap: 'border-amber-500/25 bg-amber-500/10', glow: 'bg-amber-400' },
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card, i) => (
        <StatCard key={card.label} {...card} index={i} />
      ))}
    </div>
  )
}
