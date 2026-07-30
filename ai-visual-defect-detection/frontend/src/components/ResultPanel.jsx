import { CheckCircle2, AlertTriangle, Clock, FileImage, Calendar, Gauge } from 'lucide-react'

function formatTimestamp(ts) {
  if (!ts) return '—'
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return ts
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function ConfidenceRing({ value, isGood }) {
  const clamped = Math.min(100, Math.max(0, value))
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference
  const strokeColor = isGood ? '#2dd4bf' : '#ef5548'

  return (
    <div className="relative flex h-24 w-24 shrink-0 items-center justify-center">
      <svg viewBox="0 0 96 96" className="h-24 w-24 -rotate-90">
        <circle cx="48" cy="48" r={radius} fill="none" stroke="#1b222a" strokeWidth="7" />
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          style={{ filter: `drop-shadow(0 0 6px ${strokeColor}66)` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono text-lg font-semibold tabular text-ink-100">{clamped.toFixed(0)}%</span>
        <span className="text-[9px] uppercase tracking-wider text-ink-600">Confidence</span>
      </div>
    </div>
  )
}

export default function ResultPanel({ result }) {
  if (!result) {
    return (
      <div className="relative flex h-full min-h-[300px] flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed border-base-600 bg-base-900/40 bg-blueprint bg-gridFine p-8 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg border border-base-600 bg-base-800">
          <Gauge className="h-5 w-5 text-ink-600" strokeWidth={1.75} />
        </div>
        <p className="text-sm font-medium text-ink-500">No inspection run yet</p>
        <p className="mt-1 max-w-[220px] text-xs text-ink-600">
          Upload a product image and run an AI inspection to see results here.
        </p>
      </div>
    )
  }

  const isGood = String(result.prediction).toLowerCase() !== 'defective'
  const confidence = Number(result.confidence) || 0

  return (
    <div
      className={`animate-rise flex h-full flex-col rounded-xl border p-5 shadow-panel ${
        isGood ? 'border-accent-500/30 bg-accent-500/[0.05]' : 'border-signal-red/30 bg-signal-red/[0.05]'
      }`}
    >
      <div className="flex items-center gap-4">
        <ConfidenceRing value={confidence} isGood={isGood} />
        <div className="min-w-0">
          <div
            className={`mb-1.5 inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
              isGood ? 'border-accent-500/30 bg-accent-500/10 text-accent-300' : 'border-signal-red/30 bg-signal-red/10 text-signal-red'
            }`}
          >
            {isGood ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
            Classification Result
          </div>
          <p className={`font-display text-2xl font-bold leading-none tracking-wide ${isGood ? 'text-accent-300' : 'text-signal-red'}`}>
            {isGood ? 'GOOD' : 'DEFECTIVE'}
          </p>
          <p className="mt-1.5 text-xs text-ink-600">Automated visual classification</p>
        </div>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-ink-500">Confidence Score</span>
          <span className="font-mono tabular text-ink-200">{confidence.toFixed(1)}%</span>
        </div>
        <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-base-800">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-out ${
              isGood ? 'bg-gradient-to-r from-accent-600 to-accent-400' : 'bg-gradient-to-r from-signal-redDim to-signal-red'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, confidence))}%` }}
          />
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 border-t border-base-700 pt-4 text-xs">
        <div>
          <p className="flex items-center gap-1.5 text-ink-600">
            <FileImage className="h-3.5 w-3.5" /> Filename
          </p>
          <p className="mt-1 truncate font-mono text-ink-200">{result.image_name || '—'}</p>
        </div>
        <div>
          <p className="flex items-center gap-1.5 text-ink-600">
            <Clock className="h-3.5 w-3.5" /> Processing Time
          </p>
          <p className="mt-1 font-mono tabular text-ink-200">{result.processing_time_ms ?? '—'} ms</p>
        </div>
        <div className="col-span-2">
          <p className="flex items-center gap-1.5 text-ink-600">
            <Calendar className="h-3.5 w-3.5" /> Timestamp
          </p>
          <p className="mt-1 font-mono tabular text-ink-200">{formatTimestamp(result.timestamp)}</p>
        </div>
      </div>
    </div>
  )
}
