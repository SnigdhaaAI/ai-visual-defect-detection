import { useCallback, useEffect, useState } from 'react'
import { fetchHistory } from '../api'

export function useHistory() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchHistory()
      const sorted = [...data].sort((a, b) => {
        const timeA = new Date(a.timestamp ?? 0).getTime()
        const timeB = new Date(b.timestamp ?? 0).getTime()
        return timeB - timeA
      })
      setRecords(sorted)
    } catch (err) {
      setError(err.message || 'Failed to load inspection history.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { records, loading, error, reload: load }
}
