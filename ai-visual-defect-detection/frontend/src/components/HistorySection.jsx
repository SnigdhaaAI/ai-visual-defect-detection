import { useMemo, useState } from 'react'
import { CheckCircle2, AlertTriangle, RefreshCcw, Inbox, AlertCircle, Loader2, Search } from 'lucide-react'

function formatTimestamp(ts) {
  if (!ts) return '—'
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return ts
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ResultBadge({ prediction }) {
  const isGood = String(prediction).toLowerCase() !== 'defective'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide ${
        isGood
          ? 'border-accent-500/30 bg-accent-500/10 text-accent-300'
          : 'border-signal-red/30 bg-signal-red/10 text-signal-red'
      }`}
    >
      {isGood ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
      {isGood ? 'Good' : 'Defective'}
    </span>
  )
}

export default function HistorySection({ records, loading, error, onRetry }) {
  const [query, setQuery] = useState('')

  // Purely presentational client-side filter — the underlying `records` data
  // and how it is loaded/refreshed is untouched.
  const filteredRecords = useMemo(() => {
    if (!query.trim()) return records
    const q = query.trim().toLowerCase()
    return records.filter((r) => String(r.image_name ?? '').toLowerCase().includes(q) || String(r.prediction ?? '').toLowerCase().includes(q))
  }, [records, query])

  return (
    <div className="overflow-hidden rounded-xl border border-base-600 bg-base-900/70 shadow-panel">
      <div className="flex flex-col gap-3 border-b border-base-700 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-display text-sm font-semibold tracking-wide text-ink-100">Recent Inspections</p>
          <p className="text-xs text-ink-600">Latest records from the inspection log</p>
        </div>
        <div className="flex items-center gap-2">
          {!loading && !error && records.length > 0 && (
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter records…"
                className="w-full rounded-md border border-base-600 bg-base-950 py-1.5 pl-8 pr-3 text-xs text-ink-200 placeholder:text-ink-700 focus:border-accent-500/50 sm:w-48"
              />
            </div>
          )}
          <button
            onClick={onRetry}
            className="flex shrink-0 items-center gap-1.5 rounded-md border border-base-600 px-2.5 py-1.5 text-xs font-medium text-ink-400 transition-colors hover:bg-base-800 hover:text-ink-200"
          >
            <RefreshCcw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
          <Loader2 className="h-5 w-5 animate-spin text-ink-500" />
          <p className="text-sm text-ink-500">Loading inspection history…</p>
        </div>
      )}

      {!loading && error && (
        <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
          <AlertCircle className="h-6 w-6 text-signal-red" />
          <p className="text-sm font-medium text-ink-200">Couldn't load history</p>
          <p className="max-w-[280px] text-xs text-ink-600">{error}</p>
          <button
            onClick={onRetry}
            className="mt-2 rounded-md border border-base-600 px-3 py-1.5 text-xs font-medium text-ink-300 hover:bg-base-800"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
          <Inbox className="h-6 w-6 text-ink-600" />
          <p className="text-sm font-medium text-ink-200">No inspections yet</p>
          <p className="max-w-[280px] text-xs text-ink-600">
            Run your first AI inspection above and it will appear here.
          </p>
        </div>
      )}

      {!loading && !error && records.length > 0 && filteredRecords.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
          <Search className="h-6 w-6 text-ink-600" />
          <p className="text-sm font-medium text-ink-200">No matching records</p>
          <p className="max-w-[280px] text-xs text-ink-600">Try a different filename or result.</p>
        </div>
      )}

      {!loading && !error && filteredRecords.length > 0 && (
        <>
          {/* Desktop table */}
          <div className="hidden max-h-[520px] overflow-x-auto overflow-y-auto md:block">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-10 bg-base-900/95 backdrop-blur">
                <tr className="border-b border-base-700 text-[11px] uppercase tracking-wide text-ink-600">
                  <th className="px-5 py-3 font-medium">Filename</th>
                  <th className="px-5 py-3 font-medium">Result</th>
                  <th className="px-5 py-3 font-medium">Confidence</th>
                  <th className="px-5 py-3 font-medium">Processing Time</th>
                  <th className="px-5 py-3 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record, i) => {
                  const isGood = String(record.prediction).toLowerCase() !== 'defective'
                  return (
                    <tr
                      key={record.id}
                      className={`group border-b border-base-700/60 transition-colors last:border-0 hover:bg-base-800/40 ${
                        i % 2 === 1 ? 'bg-base-950/30' : ''
                      }`}
                    >
                      <td className="relative max-w-[220px] truncate px-5 py-3 font-mono text-xs text-ink-300">
                        <span
                          className={`absolute left-0 top-0 h-full w-[2px] opacity-0 transition-opacity group-hover:opacity-100 ${
                            isGood ? 'bg-accent-400' : 'bg-signal-red'
                          }`}
                        />
                        {record.image_name}
                      </td>
                      <td className="px-5 py-3">
                        <ResultBadge prediction={record.prediction} />
                      </td>
                      <td className="px-5 py-3 font-mono tabular text-xs text-ink-300">
                        {Number(record.confidence).toFixed(1)}%
                      </td>
                      <td className="px-5 py-3 font-mono tabular text-xs text-ink-300">
                        {record.processing_time_ms} ms
                      </td>
                      <td className="px-5 py-3 font-mono tabular text-xs text-ink-500">
                        {formatTimestamp(record.timestamp)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="divide-y divide-base-700/60 md:hidden">
            {filteredRecords.map((record) => (
              <div key={record.id} className="px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate font-mono text-xs text-ink-300">{record.image_name}</p>
                  <ResultBadge prediction={record.prediction} />
                </div>
                <div className="mt-2.5 flex items-center justify-between text-xs text-ink-600">
                  <span className="font-mono tabular">{Number(record.confidence).toFixed(1)}% confidence</span>
                  <span className="font-mono tabular">{record.processing_time_ms} ms</span>
                </div>
                <p className="mt-1 font-mono tabular text-[11px] text-ink-700">{formatTimestamp(record.timestamp)}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
