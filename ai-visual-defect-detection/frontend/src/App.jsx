import { useEffect, useRef, useState } from 'react'
import { WifiOff } from 'lucide-react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import StatsCards from './components/StatsCards'
import InspectionWorkspace from './components/InspectionWorkspace'
import HistorySection from './components/HistorySection'
import { useHealth } from './hooks/useHealth'
import { useHistory } from './hooks/useHistory'

function App() {
  const health = useHealth()
  const { records, loading, error, reload } = useHistory()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('dashboard')

  const dashboardRef = useRef(null)
  const inspectionRef = useRef(null)
  const historyRef = useRef(null)
  const sectionRefs = { dashboard: dashboardRef, inspection: inspectionRef, history: historyRef }

  function handleNavigate(id) {
    setActiveSection(id)
    setMobileOpen(false)
    sectionRefs[id]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting)
        if (visible.length > 0) {
          const topMost = visible.reduce((a, b) => (a.intersectionRatio > b.intersectionRatio ? a : b))
          const id = topMost.target.getAttribute('data-section')
          if (id) setActiveSection(id)
        }
      },
      { rootMargin: '-15% 0px -60% 0px', threshold: [0.1, 0.3, 0.6] },
    )
    Object.values(sectionRefs).forEach((ref) => {
      if (ref.current) observer.observe(ref.current)
    })
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const total = records.length
  const defective = records.filter((r) => String(r.prediction).toLowerCase() === 'defective').length
  const good = total - defective

  return (
    <div className="flex h-screen overflow-hidden bg-base-950 bg-noise">
      <Sidebar
        activeSection={activeSection}
        onNavigate={handleNavigate}
        health={health}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <Header onOpenMobile={() => setMobileOpen(true)} health={health} />

        {health.status === 'offline' && (
          <div className="flex items-center gap-2 border-b border-signal-red/30 bg-signal-red/10 px-5 py-2.5 text-sm text-signal-red sm:px-8">
            <WifiOff className="h-4 w-4 shrink-0" />
            <p>Backend is unreachable at localhost:8000. Start the FastAPI server to resume live inspections.</p>
          </div>
        )}

        <main className="flex-1 space-y-12 px-5 py-8 sm:px-8">
          <section ref={dashboardRef} data-section="dashboard" className="scroll-mt-24 space-y-5">
            <div className="flex items-center gap-3">
              <div className="h-8 w-[3px] rounded-full bg-gradient-to-b from-accent-400 to-accent-600" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-accent-400">Overview</p>
                <h2 className="font-display mt-0.5 text-lg font-semibold tracking-wide text-ink-100">Dashboard</h2>
              </div>
            </div>
            <StatsCards total={total} good={good} defective={defective} />
          </section>

          <section ref={inspectionRef} data-section="inspection" className="scroll-mt-24 space-y-5">
            <div className="flex items-center gap-3">
              <div className="h-8 w-[3px] rounded-full bg-gradient-to-b from-accent-400 to-accent-600" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-accent-400">Workspace</p>
                <h2 className="font-display mt-0.5 text-lg font-semibold tracking-wide text-ink-100">Live Inspection</h2>
              </div>
            </div>
            <InspectionWorkspace onInspectionComplete={reload} />
          </section>

          <section ref={historyRef} data-section="history" className="scroll-mt-24 space-y-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-8 w-[3px] rounded-full bg-gradient-to-b from-accent-400 to-accent-600" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-accent-400">Log</p>
                <h2 className="font-display mt-0.5 text-lg font-semibold tracking-wide text-ink-100">Inspection History</h2>
              </div>
            </div>
            <HistorySection records={records} loading={loading} error={error} onRetry={reload} />
          </section>
        </main>
      </div>
    </div>
  )
}

export default App
