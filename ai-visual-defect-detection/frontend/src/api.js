// Central API client for the VisionInspect AI backend.
// Base URL is intentionally left exactly as the working backend expects.
const BASE_URL = 'http://localhost:8000'

async function parseJsonSafe(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

export async function fetchHealth() {
  const response = await fetch(`${BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`)
  }
  return parseJsonSafe(response)
}

export async function fetchHistory() {
  const response = await fetch(`${BASE_URL}/history`)
  if (!response.ok) {
    throw new Error(`Failed to load history (status ${response.status})`)
  }
  const data = await parseJsonSafe(response)
  return Array.isArray(data) ? data : data?.history ?? []
}

export async function runPrediction(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/predict`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorBody = await parseJsonSafe(response)
    const message = errorBody?.detail || errorBody?.message || `Inspection failed (status ${response.status})`
    throw new Error(message)
  }

  return parseJsonSafe(response)
}
