import { useState } from 'react'
import { testConnect, startAnalysis, executeActions } from './api/client'

/* ── tiny helpers ─────────────────────────────────────────────────────── */
const STEPS = ['Connect', 'Select', 'Analyze', 'Review', 'Execute']

function Stepper({ current }) {
  return (
    <div className="stepper">
      {STEPS.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : ''
        return (
          <div key={label} className="step-item">
            <div className={`step-circle ${state}`}>
              {i < current ? '✓' : i + 1}
            </div>
            <span className={`step-label ${state}`}>{label}</span>
            {i < STEPS.length - 1 && (
              <div className={`step-connector ${i < current ? 'done' : ''}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

function riskBadge(risk) {
  if (!risk) return null
  const cls = risk === 'SAFE' ? 'safe' : risk === 'REVIEW' ? 'review' : 'danger'
  return <span className={`badge badge-${cls}`}>{risk}</span>
}

function scoreColor(s) {
  if (s >= 80) return '#00d4aa'
  if (s >= 50) return '#f7c948'
  return '#ff5f6d'
}

function issueIcon(type) {
  const m = { duplicate: '🔁', missing: '⚠️', stale: '🕓', logic: '🔀' }
  return m[type] || '❗'
}

function execIcon(status) {
  if (!status) return '⏳'
  if (status.includes('success')) return '✅'
  if (status === 'failed') return '❌'
  return '⏳'
}

/* ── Step 1 — Connect ──────────────────────────────────────────────────── */
function StepConnect({ onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleConnect() {
    setLoading(true); setError('')
    try {
      const data = await testConnect()
      onSuccess(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-title">Connect to Smartsheet</div>
      <div className="card-desc">
        SmartAgent will connect to Smartsheet via the official Python SDK.
        In demo mode it uses WireMock — no real account needed.
      </div>

      <div style={{ marginBottom: 20 }}>
        <div className="mode-chip">🧪 Mock / WireMock mode (default)</div>
        <p className="muted" style={{ marginTop: 10 }}>
          To use a real account, set <code>USE_MOCK_SERVER=false</code> and
          add <code>SMARTSHEET_ACCESS_TOKEN</code> in <code>backend/.env</code>.
        </p>
      </div>

      {error && (
        <div className="badge badge-danger" style={{ marginBottom: 14, padding: '8px 14px', borderRadius: 8 }}>
          ⚠️ {error}
        </div>
      )}

      <button className="btn btn-primary" onClick={handleConnect} disabled={loading}>
        {loading ? <><span className="spin">⟳</span> Connecting…</> : '🔌 Connect to Smartsheet'}
      </button>
    </div>
  )
}

/* ── Step 2 — Select Sheet ─────────────────────────────────────────────── */
function StepSelect({ connectData, onSelect }) {
  const [selected, setSelected] = useState('')
  const sheets = connectData?.sheets || []

  return (
    <div className="card">
      <div className="card-title">Select a Sheet to Analyze</div>
      <div className="card-desc">
        Mode: <strong>{connectData?.mode}</strong> —{' '}
        {sheets.length} sheet{sheets.length !== 1 ? 's' : ''} available
      </div>

      <div className="field">
        <label>Sheet</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          <option value="">— pick a sheet —</option>
          {sheets.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      <button
        className="btn btn-primary"
        onClick={() => onSelect(selected, sheets.find(s => s.id === selected)?.name)}
        disabled={!selected}
      >
        🔍 Analyze This Sheet →
      </button>
    </div>
  )
}

/* ── Step 3 — Analyze ──────────────────────────────────────────────────── */
function StepAnalyze({ sheetId, onDone }) {
  const [loading, setLoading] = useState(false)
  const [started, setStarted] = useState(false)
  const [error, setError] = useState('')

  async function run() {
    setLoading(true); setStarted(true); setError('')
    try {
      const data = await startAnalysis(sheetId)
      onDone(data)
    } catch (e) {
      setError(e.message); setLoading(false); setStarted(false)
    }
  }

  const agents = [
    { name: 'Schema Intelligence', desc: 'Detecting column types & domain' },
    { name: 'Duplicate Hunter', desc: 'Finding exact duplicate rows' },
    { name: 'Quality Auditor', desc: 'Detecting empty / missing cells' },
    { name: 'Logic Validator', desc: 'Flagging invalid status values' },
    { name: 'Stale Detector', desc: 'Identifying overdue date records' },
    { name: 'Synthesizer', desc: 'Generating executive summary' },
  ]

  return (
    <div className="card">
      <div className="card-title">Running AI Analysis Pipeline</div>
      <div className="card-desc">
        LangGraph will run 6 specialist agents on sheet <strong>{sheetId}</strong>.
      </div>

      {!started && !error && (
        <button className="btn btn-primary" onClick={run}>
          🚀 Start Analysis
        </button>
      )}

      {loading && (
        <div className="loading-state">
          <div className="loading-ring" />
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Agents running…</div>
            <div className="muted">This may take 10–30 seconds</div>
          </div>
          <div className="issue-list" style={{ width: '100%' }}>
            {agents.map((a, i) => (
              <div key={a.name} className="issue-item" style={{ opacity: 0.6 + i * 0.05 }}>
                <div className="issue-icon"><span className="spin">⟳</span></div>
                <div className="issue-body">
                  <div className="issue-title">{a.name}</div>
                  <div className="issue-detail">{a.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="badge badge-danger" style={{ marginTop: 14, padding: '8px 14px', borderRadius: 8 }}>
          ⚠️ {error}
        </div>
      )}
    </div>
  )
}

/* ── Step 4 — Review (HITL) ────────────────────────────────────────────── */
function StepReview({ analysisData, onApprove }) {
  const [approved, setApproved] = useState(() =>
    (analysisData?.proposed_actions || [])
      .filter(a => a.risk_level === 'SAFE')
      .map(a => a.action_id)
  )

  const actions = analysisData?.proposed_actions || []
  const issues  = analysisData?.issues || []
  const score   = analysisData?.health_score ?? 100
  const color   = scoreColor(score)
  const pct     = `${score}%`

  function toggle(id) {
    setApproved(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  return (
    <div className="card">
      <div className="card-title">Review AI Findings</div>
      <div className="card-desc">
        Approve the actions you want SmartAgent to execute. SAFE actions are pre-selected.
      </div>

      {/* Health Score */}
      <div className="score-ring-wrap">
        <div className="score-ring" style={{ '--ring-pct': pct, '--ring-color': color }}>
          <span style={{ color }}>{score}</span>
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem' }}>Data Health Score</div>
          <div className="muted">{issues.length} issue{issues.length !== 1 ? 's' : ''} found</div>
          {analysisData?.domain && <div className="muted">Domain: {analysisData.domain}</div>}
        </div>
      </div>

      {/* Summary */}
      {analysisData?.executive_summary && (
        <div style={{
          background: 'rgba(108,99,255,0.08)',
          border: '1px solid rgba(108,99,255,0.2)',
          borderRadius: 10, padding: '12px 16px',
          fontSize: '0.85rem', color: 'var(--text-2)',
          marginBottom: 20
        }}>
          {analysisData.executive_summary}
        </div>
      )}

      {/* Issues */}
      {issues.length > 0 && (
        <>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Issues Detected</div>
          <div className="issue-list">
            {issues.slice(0, 8).map((issue, i) => (
              <div key={i} className="issue-item">
                <div className="issue-icon">{issueIcon(issue.type)}</div>
                <div className="issue-body">
                  <div className="issue-title">{issue.title || issue.type}</div>
                  <div className="issue-detail">{issue.description || issue.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="divider" />

      {/* Actions */}
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        Proposed Actions ({approved.length}/{actions.length} selected)
      </div>
      <div className="action-list">
        {actions.map(action => {
          const isApproved = approved.includes(action.action_id)
          return (
            <div
              key={action.action_id}
              className={`action-item ${isApproved ? 'approved' : ''}`}
              onClick={() => toggle(action.action_id)}
              style={{ cursor: 'pointer' }}
            >
              <div className={`action-check ${isApproved ? 'checked' : ''}`}>
                {isApproved && <span style={{ color: '#fff', fontSize: '0.75rem', fontWeight: 800 }}>✓</span>}
              </div>
              <div className="action-body">
                <div className="action-title">{action.title || action.action_type}</div>
                <div className="action-detail">{action.description}</div>
                <div className="action-badges">
                  {riskBadge(action.risk_level)}
                  {action.action_type && (
                    <span className="badge badge-info">{action.action_type}</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="divider" />
      <div className="row">
        <span className="muted">{approved.length} action{approved.length !== 1 ? 's' : ''} will execute</span>
        <div className="spacer" />
        <button
          className="btn btn-success"
          onClick={() => onApprove(approved)}
          disabled={approved.length === 0}
        >
          ✅ Execute Approved Actions →
        </button>
      </div>
    </div>
  )
}

/* ── Step 5 — Execute ──────────────────────────────────────────────────── */
function StepExecute({ analysisData, approvedIds, onReset }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function run() {
    setLoading(true); setError('')
    try {
      const payload = {
        sheet_id: analysisData.sheet_id,
        sheet_name: analysisData.sheet_name || '',
        approved_action_ids: approvedIds,
        proposed_actions: analysisData.proposed_actions || [],
        column_map: analysisData.column_map || {},
        issues: analysisData.issues || [],
        health_score: analysisData.health_score ?? 100,
      }
      const data = await executeActions(payload)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-title">Execute Approved Actions</div>
      <div className="card-desc">
        {approvedIds.length} action{approvedIds.length !== 1 ? 's' : ''} approved for execution.
      </div>

      {!result && !loading && (
        <button className="btn btn-success" onClick={run}>
          🚀 Execute Now
        </button>
      )}

      {loading && (
        <div className="loading-state">
          <div className="loading-ring" />
          <div>Applying actions via Smartsheet SDK…</div>
        </div>
      )}

      {error && (
        <div className="badge badge-danger" style={{ marginTop: 14, padding: '8px 14px', borderRadius: 8 }}>
          ⚠️ {error}
        </div>
      )}

      {result && (
        <>
          {/* Summary */}
          <div className="row" style={{ marginBottom: 20, gap: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-2)' }}>
                {result.success_count}
              </div>
              <div className="muted">Succeeded</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: result.failed_count > 0 ? 'var(--accent-err)' : 'var(--text-3)' }}>
                {result.failed_count}
              </div>
              <div className="muted">Failed</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800 }}>{result.total_executed}</div>
              <div className="muted">Total</div>
            </div>
          </div>

          {/* Audit Link */}
          {result.audit_sheet_url && (
            <a
              href={result.audit_sheet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-sm"
              style={{ marginBottom: 16, display: 'inline-flex' }}
            >
              📋 View Audit Report Sheet ↗
            </a>
          )}

          {/* Execution log */}
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Execution Log</div>
          <div className="exec-log">
            {(result.executed_actions || []).map((a, i) => (
              <div key={i} className="exec-row">
                <span className="exec-status">{execIcon(a.status)}</span>
                <span style={{ flex: 1 }}>{a.title || a.action_type || a.action_id}</span>
                <span className="muted">{a.status}</span>
              </div>
            ))}
          </div>

          <div className="divider" />
          <button className="btn btn-ghost" onClick={onReset}>
            🔄 Start New Analysis
          </button>
        </>
      )}
    </div>
  )
}

/* ── App Root ──────────────────────────────────────────────────────────── */
export default function App() {
  const [step, setStep] = useState(0)
  const [connectData, setConnectData] = useState(null)
  const [sheetId, setSheetId] = useState('')
  const [analysisData, setAnalysisData] = useState(null)
  const [approvedIds, setApprovedIds] = useState([])

  function reset() {
    setStep(0); setConnectData(null)
    setSheetId(''); setAnalysisData(null); setApprovedIds([])
  }

  return (
    <div className="app-shell">
      {/* Header */}
      <div className="header">
        <div className="header-logo">🤖</div>
        <div>
          <div className="header-title">SmartAgent</div>
          <div className="header-sub">AI-Powered Smartsheet Data Quality Auditor</div>
        </div>
      </div>

      <Stepper current={step} />

      {step === 0 && (
        <StepConnect onSuccess={data => { setConnectData(data); setStep(1) }} />
      )}
      {step === 1 && (
        <StepSelect
          connectData={connectData}
          onSelect={(id, name) => { setSheetId(id); setStep(2) }}
        />
      )}
      {step === 2 && (
        <StepAnalyze
          sheetId={sheetId}
          onDone={data => { setAnalysisData({ ...data, sheet_id: sheetId }); setStep(3) }}
        />
      )}
      {step === 3 && (
        <StepReview
          analysisData={analysisData}
          onApprove={ids => { setApprovedIds(ids); setStep(4) }}
        />
      )}
      {step === 4 && (
        <StepExecute
          analysisData={analysisData}
          approvedIds={approvedIds}
          onReset={reset}
        />
      )}
    </div>
  )
}
