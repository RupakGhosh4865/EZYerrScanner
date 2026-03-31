/**
 * EZYerrScanner API Client
 * Connects the frontend to the FastAPI backend.
 * Supports both standard file-based scanning and SmartAgent Smartsheet auditing.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// ─── File Scanner API (Original) ───────────────────────────────────────────

export async function generatePlan(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE_URL}/api/analyze/plan`, {
    method: 'POST',
    body: formData
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }))
    throw new Error(err.detail || "Plan generation failed")
  }
  return res.json()
}

export async function executeAnalysisPlan(state) {
  const res = await fetch(`${BASE_URL}/api/analyze/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Execution failed" }))
    throw new Error(err.detail || "Analysis execution failed")
  }
  return res.json()
}

// ─── SmartAgent Smartsheet API ─────────────────────────────────────────────

export async function connectToSmartsheet() {
  const res = await fetch(`${BASE_URL}/api/analyze/connect`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Connection failed" }))
    throw new Error(err.detail || "Could not connect to Smartsheet")
  }
  return res.json()  // { mode, sheets: [{id, name, row_count}], wiremock_url }
}

// ─── Step 2: Run the full LangGraph analysis on a sheet ───────────────────

export async function analyzeSheet(sheetId) {
  const res = await fetch(`${BASE_URL}/api/analyze/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sheet_id: sheetId })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }))
    throw new Error(err.detail || "Analysis failed")
  }
  // Returns: { sheet_name, health_score, domain, issues, proposed_actions,
  //            agent_statuses, executive_summary, top_priorities, column_map }
  return res.json()
}

// ─── Step 3: Execute approved actions (HITL) ──────────────────────────────

export async function executeActions({
  sheetId,
  approvedActionIds,
  proposedActions,
  columnMap,
  issues,
  healthScore,
  sheetName
}) {
  const res = await fetch(`${BASE_URL}/api/actions/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sheet_id: sheetId,
      approved_action_ids: approvedActionIds,
      proposed_actions: proposedActions,
      column_map: columnMap,
      issues: issues,
      health_score: healthScore,
      sheet_name: sheetName
    })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Execution failed" }))
    throw new Error(err.detail || "Action execution failed")
  }
  // Returns: { executed_actions, audit_sheet_url, total_executed, success_count, failed_count }
  return res.json()
}

export async function downloadCorrectedCsv({
  sheetId,
  approvedActionIds,
  proposedActions,
  columnMap,
  sheetName
}) {
  const res = await fetch(`${BASE_URL}/api/actions/download_csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sheet_id: sheetId,
      approved_action_ids: approvedActionIds,
      proposed_actions: proposedActions,
      column_map: columnMap,
      sheet_name: sheetName
    })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "CSV download failed" }))
    throw new Error(err.detail || "CSV download failed")
  }
  return res.blob()
}
