import { useEffect, useState } from 'react'
import { Menu, Wifi, WifiOff, Cpu, Clock } from 'lucide-react'
import StatusPill from './StatusPill'

function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

export default function Header({ onOpenMobile, health }) {
  const isOnline = health.status === 'online'
  const isChecking = health.status === 'checking'
  const now = useClock()

  return (
    <header className="sticky top-0 z-30 border-b border-base-700 bg-base-950/85 backdrop-blur-md">
      {/* Top thin utility bar */}
      <div className="hidden items-center justify-between border-b border-base-800/80 px-8 py-1.5 text-[10.5px] uppercase tracking-wider text-ink-700 md:flex">
        <p>Manufacturing &nbsp;/&nbsp; Quality Control &nbsp;/&nbsp; <span className="text-ink-500">Vision Inspection Station</span></p>
        <p className="flex items-center gap-1.5 font-mono tabular text-ink-600">
          <Clock className="h-3 w-3" />
          {now.toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })} &middot;{' '}
          {now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </p>
      </div>

      <div className="flex items-center gap-4 px-5 py-4 sm:px-8">
        <button
          onClick={onOpenMobile}
          className="rounded-md border border-base-600 p-2 text-ink-300 hover:bg-base-800 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="min-w-0 flex-1">
          <h1 className="font-display truncate text-[19px] font-semibold tracking-wide text-ink-100 sm:text-[22px]">
            Visual Quality Inspection
          </h1>
          <p className="mt-0.5 hidden text-sm text-ink-500 sm:block">
            AI-powered manufacturing defect detection and automated quality control
          </p>
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <StatusPill
            tone={isOnline ? 'good' : isChecking ? 'pending' : 'bad'}
            label={isOnline ? 'API Online' : isChecking ? 'Checking' : 'API Offline'}
            animated={isChecking}
          />
          <StatusPill
            tone={isOnline && health.modelReady ? 'good' : 'bad'}
            label={isOnline && health.modelReady ? 'Model Ready' : 'Model Unavailable'}
          />
        </div>

        <div className="flex items-center gap-1.5 rounded-lg border border-base-600 bg-base-900 px-2.5 py-1.5 md:hidden">
          {isOnline ? (
            <Wifi className="h-4 w-4 text-accent-400" />
          ) : (
            <WifiOff className="h-4 w-4 text-signal-red" />
          )}
          <Cpu className={`h-4 w-4 ${isOnline && health.modelReady ? 'text-accent-400' : 'text-signal-red'}`} />
        </div>
      </div>
    </header>
  )
}
