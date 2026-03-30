import { useState, useEffect, useRef } from 'react'
import { connectToSmartsheet, analyzeSheet, executeActions } from './api/client'
import AgentTimeline from './components/AgentTimeline'
import IssueCard from './components/IssueCard'
import ReportSummary from './components/ReportSummary'
import {
  Bot, Shield, Rocket, CheckCircle, ChevronRight,
  Zap, Database, AlertTriangle, Play, RefreshCw,
  ExternalLink, ThumbsUp, ThumbsDown
} from 'lucide-react'

// ─── Step indicator ────────────────────────────────────────────────────────────
const STEPS = ['Connect', 'Select Sheet', 'Analyze', 'Review Actions', 'Execute']

function StepBar({ current }) {
  return (
    <div className="step-bar">
      {STEPS.map((label, i) => (
        <div key={label} className={`step-tab ${i === current ? 'active' : i < current ? 'done' : ''}`}>
          {i < current ? <CheckCircle size={13} /> : <span>{i + 1}</span>}
          <span className="step-label">{label}</span>
          {i < STEPS.length - 1 && <ChevronRight size={12} className="step-arrow" />}
        </div>
      ))}
    </div>
  )
}

// ─── Loading spinner card ──────────────────────────────────────────────────────
function LoadingCard({ message, subtext }) {
  const agents = [
    "Schema Intelligence → detecting column types...",
    "Supervisor → routing to specialist agents...",
    "Duplicate Hunter → scanning row fingerprints...",
    "Quality Auditor → checking for empty cells...",
    "Logic Validator → verifying status values...",
    "Stale Detector → flagging outdated records...",
    "Aggregator → computing health score...",
    "Synthesizer → generating executive summary..."
  ]
  const [agentIdx, setAgentIdx] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setAgentIdx(i => (i + 1) % agents.length), 1100)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="loading-steps glass-panel" style={{ border: '1px solid var(--neon-blue)', boxShadow: '0 0 24px var(--neon-glow)' }}>
      <div className="loader" style={{ borderTopColor: 'var(--neon-blue)' }} />
      <div className="loading-text" style={{ fontFamily: 'Orbitron', letterSpacing: '1px', minHeight: '1.6em' }}>
        {message}
      </div>
      {subtext && (
        <div style={{ fontSize: '0.72rem', color: 'var(--neon-blue)', marginTop: '8px', letterSpacing: '1.5px', opacity: 0.75 }}>
          {subtext === 'agents' ? agents[agentIdx] : subtext}
        </div>
      )}
    </div>
  )
}

// ─── Risk badge ────────────────────────────────────────────────────────────────
function RiskBadge({ level }) {
  const color = { SAFE: '#00ff87', REVIEW: '#ffd700', DESTRUCTIVE: '#ff4466' }[level] || '#ccc'
  return <span style={{ color, border: `1px solid ${color}`, borderRadius: 4, padding: '1px 7px', fontSize: '0.68rem', marginLeft: 8, fontFamily: 'Orbitron' }}>{level}</span>
}

// ─── Action row in HITL panel ─────────────────────────────────────────────────
function ActionRow({ action, approved, onToggle }) {
  return (
    <div className={`action-row ${approved ? 'approved' : ''}`} onClick={() => onToggle(action.action_id)}>
      <div className="action-left">
        <div className="action-toggle">{approved ? <ThumbsUp size={14} color="#00ff87" /> : <ThumbsDown size={14} color="#666" />}</div>
        <div>
          <div className="action-title">
            <span style={{ fontFamily: 'Orbitron', fontSize: '0.75rem' }}>{action.action_type.replace(/_/g, ' ').toUpperCase()}</span>
            <RiskBadge level={action.risk_level} />
          </div>
          <div className="action-desc">{action.reason}</div>
          {action.proposed_value && (
            <div className="action-value">→ {action.proposed_value.slice(0, 120)}</div>
          )}
        </div>
      </div>
      <div className="action-agent" style={{ color: 'var(--text-grey)', fontSize: '0.68rem' }}>
        {action.agent}
      </div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [step, setStep] = useState(0)         // 0-4
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [loadingSub, setLoadingSub] = useState('')
  const [error, setError] = useState(null)

  // Step 0 – connect
  const [mode, setMode] = useState(null)
  const [sheets, setSheets] = useState([])

  // Step 1 – select
  const [selectedSheet, setSelectedSheet] = useState(null)

  // Step 2 – analysis result
  const [analysis, setAnalysis] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Step 3 – HITL action approval
  const [approvedIds, setApprovedIds] = useState(new Set())

  // Step 4 – execution result
  const [execution, setExecution] = useState(null)

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleConnect = async () => {
    setLoading(true); setLoadingMsg('Connecting to Smartsheet...'); setError(null)
    try {
      const data = await connectToSmartsheet()
      setMode(data.mode); setSheets(data.sheets)
      setStep(1)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const handleSelectSheet = (sheet) => {
    setSelectedSheet(sheet); setStep(2)
    handleAnalyze(sheet.id)
  }

  const handleAnalyze = async (sheetId) => {
    setLoading(true); setLoadingMsg('Running LangGraph pipeline...')
    setLoadingSub('agents'); setError(null); setAnalysis(null)
    try {
      const data = await analyzeSheet(sheetId)
      setAnalysis(data)
      // Pre-approve all SAFE actions
      const safeIds = new Set(data.proposed_actions.filter(a => a.risk_level === 'SAFE').map(a => a.action_id))
      setApprovedIds(safeIds)
      setStep(3)
    } catch (e) { setError(e.message) } finally { setLoading(false); setLoadingSub('') }
  }

  const toggleAction = (id) => {
    setApprovedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleExecute = async () => {
    setLoading(true); setLoadingMsg('Executing approved actions via Smartsheet SDK...')
    setLoadingSub('Writing to WireMock...'); setError(null)
    try {
      const result = await executeActions({
        sheetId: selectedSheet.id,
        approvedActionIds: [...approvedIds],
        proposedActions: analysis.proposed_actions,
        columnMap: analysis.column_map || {},
        issues: analysis.issues,
        healthScore: analysis.health_score,
        sheetName: analysis.sheet_name
      })
      setExecution(result); setStep(4)
    } catch (e) { setError(e.message) } finally { setLoading(false); setLoadingSub('') }
  }

  const handleReset = () => {
    setStep(0); setMode(null); setSheets([]); setSelectedSheet(null)
    setAnalysis(null); setExecution(null); setApprovedIds(new Set())
    setError(null)
  }

  // Derived issue list
  const issues = analysis?.issues || []
  const filteredIssues = issues.filter(iss => {
    const ok1 = severityFilter === 'ALL' || iss.severity === severityFilter
    const ok2 = iss.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                iss.description?.toLowerCase().includes(searchQuery.toLowerCase())
    return ok1 && ok2
  })
  const sorted = [...filteredIssues].sort((a, b) => ({ HIGH: 0, MEDIUM: 1, LOW: 2 }[a.severity] ?? 3) - ({ HIGH: 0, MEDIUM: 1, LOW: 2 }[b.severity] ?? 3))

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <main className="main-content" style={{ maxWidth: 960, margin: '0 auto', padding: '0 1.5rem' }}>

        {/* Header */}
        <header className="header-meta" style={{ marginBottom: '0.5rem' }}>
          <div className="live-status">
            <div className="status-dot" />
            SMARTAGENT: {loading ? loadingMsg.toUpperCase() : step === 4 ? 'EXECUTION_COMPLETE' : step === 0 ? 'SYSTEM_READY' : 'ACTIVE'}
          </div>
          <button onClick={handleReset} style={{ background: 'transparent', border: '1px solid var(--border-neon)', color: 'var(--text-grey)', borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: '0.72rem' }}>
            ↺ Reset
          </button>
        </header>

        {/* Step bar */}
        <StepBar current={step} />

        <div className="dashboard-container" style={{ marginTop: '1.5rem' }}>

          {error && (
            <div className="error-container">
              <h3 className="error-title">Error</h3>
              <div className="error-body"><p>{error}</p></div>
              <button className="error-retry-btn" onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}

          {loading && <LoadingCard message={loadingMsg} subtext={loadingSub} />}

          {/* ── STEP 0: Connect ─────────────────────────────────────────── */}
          {!loading && step === 0 && (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
              <Bot size={60} color="var(--neon-blue)" style={{ marginBottom: '1.5rem' }} />
              <h1 style={{ fontFamily: 'Orbitron', fontSize: '1.6rem', marginBottom: '0.8rem' }}>
                SmartAgent
              </h1>
              <p style={{ color: 'var(--text-grey)', marginBottom: '0.5rem', maxWidth: 520, margin: '0 auto 0.5rem' }}>
                AI-powered data quality agent for Smartsheet. Detects duplicates, missing data, logic errors, and stale records — then proposes corrective actions for your approval.
              </p>
              <p style={{ color: 'var(--neon-blue)', fontSize: '0.75rem', marginBottom: '2.5rem', fontFamily: 'Orbitron', letterSpacing: '1px' }}>
                MODE: {mode || 'WIREMOCK_READY'} • SDK: OFFICIAL SMARTSHEET PYTHON SDK
              </p>
              <button className="approve-btn" onClick={handleConnect} id="btn-connect">
                <Database size={18} style={{ marginRight: 10 }} />
                Connect to Smartsheet
              </button>
            </div>
          )}

          {/* ── STEP 1: Select Sheet ─────────────────────────────────────── */}
          {!loading && step === 1 && (
            <div className="glass-panel">
              <div className="node-title">
                <Database size={18} color="var(--neon-blue)" />
                Select a Sheet to Audit
                <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--neon-blue)', fontFamily: 'Orbitron' }}>
                  MODE: {mode?.toUpperCase()}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
                {sheets.map(sheet => (
                  <button
                    key={sheet.id}
                    id={`sheet-${sheet.id}`}
                    onClick={() => handleSelectSheet(sheet)}
                    style={{
                      background: 'rgba(0,200,255,0.04)', border: '1px solid var(--border-neon)',
                      borderRadius: 8, padding: '1rem 1.25rem', textAlign: 'left', cursor: 'pointer',
                      transition: 'all 0.2s', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '1rem'
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--neon-blue)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-neon)'}
                  >
                    <Shield size={22} color="var(--neon-blue)" />
                    <div>
                      <div style={{ fontFamily: 'Orbitron', fontSize: '0.9rem' }}>{sheet.name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-grey)', marginTop: 3 }}>
                        ID: {sheet.id} • Rows: {sheet.row_count ?? '—'}
                      </div>
                    </div>
                    <ChevronRight size={18} style={{ marginLeft: 'auto', color: 'var(--text-grey)' }} />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── STEP 2 used for loading only (handleAnalyze redirects to step 3) ── */}

          {/* ── STEP 3: Review Analysis + HITL Actions ───────────────────── */}
          {!loading && step === 3 && analysis && (
            <div className="result-view" style={{ animation: 'slideUp 0.5s ease' }}>

              {/* Summary Panel */}
              <div className="node-title">
                <Shield size={18} color="var(--neon-blue)" />
                Analysis Complete — {analysis.sheet_name}
              </div>
              <ReportSummary report={analysis} />
              <AgentTimeline agentStatuses={analysis.agent_statuses || []} />

              {/* Executive Summary */}
              {analysis.executive_summary && (
                <div className="glass-panel" style={{ marginTop: '1.5rem', borderLeft: '3px solid var(--neon-blue)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--neon-blue)', fontFamily: 'Orbitron', marginBottom: 8 }}>EXECUTIVE SUMMARY</div>
                  <p style={{ color: 'var(--text-primary)', lineHeight: 1.7, fontSize: '0.9rem' }}>{analysis.executive_summary}</p>
                </div>
              )}

              {/* Issues */}
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ fontFamily: 'Orbitron', fontSize: '1.1rem', borderBottom: '1px solid var(--border-neon)', paddingBottom: '0.6rem', marginBottom: '1rem' }}>
                  AI Findings ({issues.length})
                </h2>
                <div className="issue-tabs">
                  {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(lvl => (
                    <button key={lvl} className={`issue-tab ${severityFilter === lvl ? 'active' : ''}`} onClick={() => setSeverityFilter(lvl)}>
                      {lvl === 'ALL' ? `All (${issues.length})` : `${lvl} (${issues.filter(i => i.severity === lvl).length})`}
                    </button>
                  ))}
                </div>
                <input type="text" className="search-input" placeholder="Filter findings..." value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'var(--border-neon)', marginBottom: '1rem' }} />
                <div className="issue-list">
                  {sorted.map((iss, idx) => <IssueCard key={`${iss.id}-${idx}`} issue={iss} />)}
                  {sorted.length === 0 && (
                    <div style={{ textAlign: 'center', color: 'var(--text-grey)', padding: '2rem', fontFamily: 'Orbitron', fontSize: '0.8rem' }}>
                      NO ISSUES MATCH CURRENT FILTER
                    </div>
                  )}
                </div>
              </div>

              {/* HITL Action Review Panel */}
              {analysis.proposed_actions?.length > 0 && (
                <div className="glass-panel" style={{ marginTop: '2rem', border: '1px solid var(--neon-blue)' }}>
                  <div className="node-title" style={{ marginBottom: '0.5rem' }}>
                    <Zap size={18} color="var(--neon-blue)" />
                    Proposed Actions — Human-in-the-Loop Review
                    <span style={{ marginLeft: 'auto', fontFamily: 'Orbitron', fontSize: '0.68rem', color: 'var(--text-grey)' }}>
                      {approvedIds.size}/{analysis.proposed_actions.length} APPROVED
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-grey)', fontSize: '0.8rem', marginBottom: '1rem' }}>
                    Click to toggle approval. SAFE actions are pre-approved. REVIEW and DESTRUCTIVE actions require explicit approval.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {analysis.proposed_actions.map(action => (
                      <ActionRow key={action.action_id} action={action} approved={approvedIds.has(action.action_id)} onToggle={toggleAction} />
                    ))}
                  </div>
                  <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                    <button className="approve-btn" id="btn-execute-actions" onClick={handleExecute}
                      disabled={approvedIds.size === 0}
                      style={{ opacity: approvedIds.size === 0 ? 0.4 : 1 }}>
                      <Play size={16} style={{ marginRight: 8 }} />
                      Execute {approvedIds.size} Approved Action{approvedIds.size !== 1 ? 's' : ''} via Smartsheet SDK
                    </button>
                    <button onClick={() => setApprovedIds(new Set(analysis.proposed_actions.map(a => a.action_id)))}
                      style={{ background: 'transparent', border: '1px solid var(--border-neon)', color: 'var(--text-grey)', borderRadius: 8, padding: '0.75rem 1.25rem', cursor: 'pointer', fontSize: '0.8rem' }}>
                      Approve All
                    </button>
                    <button onClick={() => setApprovedIds(new Set())}
                      style={{ background: 'transparent', border: '1px solid var(--border-neon)', color: 'var(--text-grey)', borderRadius: 8, padding: '0.75rem 1.25rem', cursor: 'pointer', fontSize: '0.8rem' }}>
                      Reject All
                    </button>
                  </div>
                </div>
              )}

              {analysis.proposed_actions?.length === 0 && (
                <div className="glass-panel" style={{ marginTop: '1.5rem', textAlign: 'center', padding: '2rem' }}>
                  <CheckCircle size={40} color="#00ff87" style={{ marginBottom: '1rem' }} />
                  <p style={{ fontFamily: 'Orbitron', color: '#00ff87' }}>NO CORRECTIVE ACTIONS NEEDED</p>
                  <p style={{ color: 'var(--text-grey)', marginTop: 8, fontSize: '0.85rem' }}>Sheet data quality is clean.</p>
                </div>
              )}
            </div>
          )}

          {/* ── STEP 4: Execution Result ─────────────────────────────────── */}
          {!loading && step === 4 && execution && (
            <div className="result-view" style={{ animation: 'slideUp 0.5s ease' }}>
              <div className="node-title">
                <CheckCircle size={18} color="#00ff87" />
                Execution Complete
              </div>

              {/* Stats row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                  { label: 'Total Executed', value: execution.total_executed, color: 'var(--neon-blue)' },
                  { label: 'Successful', value: execution.success_count, color: '#00ff87' },
                  { label: 'Failed', value: execution.failed_count, color: execution.failed_count > 0 ? '#ff4466' : 'var(--text-grey)' },
                ].map(stat => (
                  <div key={stat.label} className="glass-panel" style={{ textAlign: 'center', padding: '1.25rem' }}>
                    <div style={{ fontSize: '2.5rem', fontFamily: 'Orbitron', color: stat.color }}>{stat.value}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-grey)', marginTop: 4 }}>{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Audit sheet link */}
              {execution.audit_sheet_url && (
                <div className="glass-panel" style={{ borderLeft: '3px solid #00ff87', marginBottom: '1.5rem' }}>
                  <div style={{ fontFamily: 'Orbitron', fontSize: '0.75rem', color: '#00ff87', marginBottom: 6 }}>AUDIT SHEET CREATED</div>
                  <a href={execution.audit_sheet_url} target="_blank" rel="noopener noreferrer"
                    style={{ color: 'var(--neon-blue)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <ExternalLink size={14} /> {execution.audit_sheet_url}
                  </a>
                </div>
              )}

              {/* Action log */}
              <div className="glass-panel">
                <div style={{ fontFamily: 'Orbitron', fontSize: '0.75rem', color: 'var(--neon-blue)', marginBottom: '1rem' }}>
                  EXECUTION LOG
                </div>
                {execution.executed_actions?.map((ea, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    padding: '0.6rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)',
                    fontSize: '0.82rem'
                  }}>
                    {ea.status === 'success'
                      ? <CheckCircle size={14} color="#00ff87" />
                      : <AlertTriangle size={14} color="#ff4466" />}
                    <span style={{ fontFamily: 'Orbitron', fontSize: '0.7rem', color: ea.status === 'success' ? '#00ff87' : '#ff4466' }}>
                      {ea.status.toUpperCase()}
                    </span>
                    <span style={{ color: 'var(--text-primary)' }}>{ea.action_type.replace(/_/g, ' ')}</span>
                    <span style={{ color: 'var(--text-grey)', fontSize: '0.68rem', marginLeft: 'auto' }}>
                      {ea.executed_at?.split('T')[1]?.slice(0, 8)} UTC
                    </span>
                  </div>
                ))}
                {!execution.executed_actions?.length && (
                  <p style={{ color: 'var(--text-grey)', fontSize: '0.85rem' }}>No actions were executed.</p>
                )}
              </div>

              {/* Restart */}
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button className="approve-btn" onClick={handleReset}>
                  <RefreshCw size={16} style={{ marginRight: 8 }} />
                  Audit Another Sheet
                </button>
              </div>
            </div>
          )}

        </div>
      </main>
    </>
  )
}
