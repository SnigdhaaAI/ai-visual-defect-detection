import { useState } from 'react'
import { LayoutGrid, ScanLine, History, X, Aperture, ChevronsLeft, ChevronsRight } from 'lucide-react'
import StatusPill from './StatusPill'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
  { id: 'inspection', label: 'Live Inspection', icon: ScanLine },
  { id: 'history', label: 'Inspection History', icon: History },
]

export default function Sidebar({ activeSection, onNavigate, health, mobileOpen, onCloseMobile }) {
  const [collapsed, setCollapsed] = useState(false)

  const content = (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div className={`flex items-center gap-3 border-b border-base-700/80 px-5 py-6 ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}>
        <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-accent-500/30 bg-accent-500/10">
          <Aperture className="h-5 w-5 text-accent-400" strokeWidth={1.75} />
          <span className="absolute inset-0 rounded-lg border border-accent-400/20 animate-pulseRing" />
        </div>
        <div className={`min-w-0 leading-tight ${collapsed ? 'lg:hidden' : ''}`}>
          <p className="font-display truncate text-[15px] font-semibold tracking-wide text-ink-100">
            VisionInspect <span className="text-accent-400">AI</span>
          </p>
          <p className="text-[10.5px] uppercase tracking-wider text-ink-600">Quality Control System</p>
        </div>
        <button
          onClick={onCloseMobile}
          className="ml-auto rounded-md p-1.5 text-ink-500 hover:bg-base-800 hover:text-ink-100 lg:hidden"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-5">
        {!collapsed && (
          <p className="mb-2 px-3 text-[10.5px] font-semibold uppercase tracking-wider text-ink-700">Navigation</p>
        )}
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = activeSection === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              title={collapsed ? item.label : undefined}
              className={`group relative flex w-full items-center gap-3 rounded-lg border px-3.5 py-2.5 text-left text-sm transition-all duration-200 ${
                collapsed ? 'lg:justify-center lg:px-0' : ''
              } ${
                isActive
                  ? 'border-accent-500/25 bg-accent-500/[0.09] text-ink-100 shadow-[0_0_0_1px_rgba(63,214,200,0.06)]'
                  : 'border-transparent text-ink-500 hover:border-base-600 hover:bg-base-800/60 hover:text-ink-300'
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-accent-400" />
              )}
              <Icon
                className={`h-[18px] w-[18px] shrink-0 transition-colors ${
                  isActive ? 'text-accent-400' : 'text-ink-600 group-hover:text-ink-300'
                }`}
                strokeWidth={1.75}
              />
              <span className={`font-medium ${collapsed ? 'lg:hidden' : ''}`}>{item.label}</span>
              {isActive && <span className={`ml-auto h-1.5 w-1.5 rounded-full bg-accent-400 ${collapsed ? 'lg:hidden' : ''}`} />}
            </button>
          )
        })}
      </nav>

      {/* System status */}
      <div className={`mx-3 mb-3 rounded-xl border border-base-600 bg-base-900/60 p-4 ${collapsed ? 'lg:hidden' : ''}`}>
        <p className="mb-3 flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-600">
          <span className="h-1 w-1 rounded-full bg-ink-600" />
          System Status
        </p>
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-ink-500">API Server</span>
            <StatusPill
              tone={health.status === 'online' ? 'good' : health.status === 'offline' ? 'bad' : 'pending'}
              label={health.status === 'online' ? 'Online' : health.status === 'offline' ? 'Offline' : 'Checking'}
              animated={health.status === 'checking'}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-ink-500">AI Model</span>
            <StatusPill
              tone={health.status === 'online' && health.modelReady ? 'good' : 'bad'}
              label={health.status === 'online' && health.modelReady ? 'Ready' : 'Unavailable'}
            />
          </div>
        </div>
      </div>

      {/* Collapse toggle - desktop only */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="mx-3 mb-4 hidden items-center justify-center gap-2 rounded-lg border border-base-700 py-2 text-xs font-medium text-ink-600 transition-colors hover:border-base-500 hover:text-ink-300 lg:flex"
      >
        {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        {!collapsed && 'Collapse'}
      </button>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`relative hidden shrink-0 border-r border-base-700 bg-base-900/90 transition-[width] duration-300 ease-out lg:block ${
          collapsed ? 'w-[76px]' : 'w-[268px]'
        }`}
      >
        {content}
      </aside>

      {/* Mobile slide-over */}
      <div
        className={`fixed inset-0 z-40 lg:hidden ${mobileOpen ? '' : 'pointer-events-none'}`}
        aria-hidden={!mobileOpen}
      >
        <div
          className={`absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity duration-300 ${
            mobileOpen ? 'opacity-100' : 'opacity-0'
          }`}
          onClick={onCloseMobile}
        />
        <aside
          className={`absolute left-0 top-0 h-full w-[280px] border-r border-base-700 bg-base-900 shadow-2xl transition-transform duration-300 ease-out ${
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {content}
        </aside>
      </div>
    </>
  )
}
