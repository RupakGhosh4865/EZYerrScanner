const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function testConnect() {
  const res = await fetch(`${BASE}/api/analyze/connect`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function startAnalysis(sheetId) {
  const res = await fetch(`${BASE}/api/analyze/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sheet_id: sheetId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function executeActions(payload) {
  const res = await fetch(`${BASE}/api/actions/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
