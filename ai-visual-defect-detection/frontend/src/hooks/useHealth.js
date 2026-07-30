import { useEffect, useRef, useState } from 'react'
import { fetchHealth } from '../api'

const POLL_INTERVAL_MS = 15000

export function useHealth() {
  const [status, setStatus] = useState('checking') // 'checking' | 'online' | 'offline'
  const [modelReady, setModelReady] = useState(false)
  const [lastChecked, setLastChecked] = useState(null)
  const timerRef = useRef(null)

  async function check() {
    try {
      const data = await fetchHealth()
      setStatus('online')
      const ready =
        data?.model_ready ??
        data?.modelReady ??
        data?.model_loaded ??
        (typeof data?.status === 'string' ? data.status.toLowerCase() === 'ok' : true)
      setModelReady(Boolean(ready))
    } catch {
      setStatus('offline')
      setModelReady(false)
    } finally {
      setLastChecked(new Date())
    }
  }

  useEffect(() => {
    check()
    timerRef.current = setInterval(check, POLL_INTERVAL_MS)
    return () => clearInterval(timerRef.current)
  }, [])

  return { status, modelReady, lastChecked, refresh: check }
}
