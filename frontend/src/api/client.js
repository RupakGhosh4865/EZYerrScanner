/**
 * SmartAgent API Client
 * Connects the frontend to the FastAPI backend.
 * Supports both WireMock (dev) and real Smartsheet (prod).
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// ─── Step 1: Test Smartsheet connectivity ─────────────────────────────────

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
