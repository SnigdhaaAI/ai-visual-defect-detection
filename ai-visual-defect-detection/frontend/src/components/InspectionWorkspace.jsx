import { useCallback, useRef, useState } from 'react'
import { UploadCloud, ImagePlus, X, ScanLine, Loader2, AlertCircle, FileCheck2 } from 'lucide-react'
import ResultPanel from './ResultPanel'
import { runPrediction } from '../api'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
const MAX_SIZE_MB = 10

function formatBytes(bytes) {
  if (!bytes) return '0 KB'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  return `${(kb / 1024).toFixed(2)} MB`
}

export default function InspectionWorkspace({ onInspectionComplete }) {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleFile = useCallback((incoming) => {
    if (!incoming) return
    if (!ACCEPTED_TYPES.includes(incoming.type)) {
      setError('Unsupported file type. Please upload a JPEG or PNG image.')
      return
    }
    if (incoming.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      return
    }
    setError(null)
    setResult(null)
    setFile(incoming)
    setPreviewUrl(URL.createObjectURL(incoming))
  }, [])

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    handleFile(dropped)
  }

  function handleRemove() {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  async function handleRunInspection() {
    if (!file || isRunning) return
    setIsRunning(true)
    setError(null)
    try {
      const data = await runPrediction(file)
      setResult(data)
      onInspectionComplete?.()
    } catch (err) {
      setError(err.message || 'Inspection failed. Please try again.')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
      {/* Upload panel */}
      <div className="lg:col-span-3">
        <div className="relative overflow-hidden rounded-xl border border-base-600 bg-base-900/70 p-5 shadow-panel">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent-400/40 to-transparent" />

          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="font-display text-sm font-semibold tracking-wide text-ink-100">Inspection Input</p>
              <p className="text-xs text-ink-600">Supports JPEG and PNG, up to {MAX_SIZE_MB} MB</p>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-md border border-base-600 bg-base-800">
              <ScanLine className="h-4 w-4 text-accent-400" strokeWidth={1.75} />
            </div>
          </div>

          {!previewUrl ? (
            <label
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`relative flex min-h-[300px] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-lg border-2 border-dashed px-6 py-10 text-center transition-all duration-300 bg-blueprint bg-grid ${
                isDragging
                  ? 'scale-[0.99] border-accent-400/70 bg-accent-500/[0.05]'
                  : 'border-base-600 hover:border-base-500 hover:bg-base-800/40'
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png"
                className="sr-only"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
              <div
                className={`mb-4 flex h-16 w-16 items-center justify-center rounded-full border transition-all duration-300 ${
                  isDragging ? 'border-accent-400/50 bg-accent-500/10 animate-floatSlow' : 'border-base-600 bg-base-800'
                }`}
              >
                <UploadCloud className={`h-7 w-7 transition-colors ${isDragging ? 'text-accent-400' : 'text-ink-500'}`} strokeWidth={1.5} />
              </div>
              <p className="text-sm font-medium text-ink-200">Drag and drop a product image</p>
              <p className="mt-1 text-xs text-ink-600">or click to browse your files</p>
              <div className="mt-5 flex items-center gap-2 text-[10.5px] uppercase tracking-wider text-ink-700">
                <span className="rounded border border-base-600 px-1.5 py-0.5">JPEG</span>
                <span className="rounded border border-base-600 px-1.5 py-0.5">PNG</span>
                <span className="rounded border border-base-600 px-1.5 py-0.5">≤ {MAX_SIZE_MB}MB</span>
              </div>
            </label>
          ) : (
            <div className="animate-rise relative overflow-hidden rounded-lg border border-base-600 bg-base-950">
              <div className="relative flex min-h-[300px] items-center justify-center overflow-hidden bg-base-950 bg-blueprint bg-gridFine p-3">
                <img src={previewUrl} alt="Selected product for inspection" className="max-h-[320px] rounded-md object-contain" />
                {/* Corner bracket framing — signature motif */}
                <div className="pointer-events-none absolute inset-3 rounded-md">
                  <span className="absolute left-0 top-0 h-5 w-5 rounded-tl-md border-l-2 border-t-2 border-accent-400/70" />
                  <span className="absolute right-0 top-0 h-5 w-5 rounded-tr-md border-r-2 border-t-2 border-accent-400/70" />
                  <span className="absolute bottom-0 left-0 h-5 w-5 rounded-bl-md border-b-2 border-l-2 border-accent-400/70" />
                  <span className="absolute bottom-0 right-0 h-5 w-5 rounded-br-md border-b-2 border-r-2 border-accent-400/70" />
                </div>
                {isRunning && (
                  <>
                    <div className="absolute inset-x-3 top-3 h-full overflow-hidden rounded-md">
                      <div className="absolute left-0 top-0 h-1/3 w-full animate-scan bg-gradient-to-b from-transparent via-accent-400/30 to-transparent" />
                    </div>
                    <div className="absolute bottom-5 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full border border-accent-500/30 bg-base-950/90 px-3 py-1.5 text-[11px] font-medium text-accent-300 backdrop-blur">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Analyzing surface features…
                    </div>
                  </>
                )}
                {!isRunning && result && (
                  <div className="absolute right-4 top-4 flex items-center gap-1.5 rounded-full border border-base-600 bg-base-950/90 px-2.5 py-1 text-[10.5px] font-medium text-ink-300 backdrop-blur">
                    <FileCheck2 className="h-3 w-3 text-accent-400" />
                    Processed
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between gap-3 border-t border-base-700 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink-200">{file.name}</p>
                  <p className="text-xs text-ink-600">{formatBytes(file.size)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <label className="cursor-pointer rounded-md border border-base-600 px-3 py-1.5 text-xs font-medium text-ink-300 transition-colors hover:bg-base-800">
                    Change
                    <input
                      type="file"
                      accept="image/jpeg,image/png"
                      className="sr-only"
                      onChange={(e) => handleFile(e.target.files?.[0])}
                    />
                  </label>
                  <button
                    onClick={handleRemove}
                    className="flex items-center gap-1 rounded-md border border-base-600 px-3 py-1.5 text-xs font-medium text-ink-300 transition-colors hover:border-signal-red/40 hover:bg-signal-red/10 hover:text-signal-red"
                  >
                    <X className="h-3.5 w-3.5" />
                    Remove
                  </button>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="animate-rise mt-4 flex items-start gap-2 rounded-lg border border-signal-red/30 bg-signal-red/10 px-3.5 py-3 text-sm text-signal-red">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <button
            onClick={handleRunInspection}
            disabled={!file || isRunning}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-accent-500 px-4 py-3 text-sm font-semibold text-base-950 shadow-glow transition-all duration-200 hover:bg-accent-400 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-base-700 disabled:text-ink-600 disabled:shadow-none"
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running AI Inspection…
              </>
            ) : (
              <>
                <ImagePlus className="h-4 w-4" />
                Run AI Inspection
              </>
            )}
          </button>
        </div>
      </div>

      {/* Result panel */}
      <div className="lg:col-span-2">
        <ResultPanel result={result} />
      </div>
    </div>
  )
}
