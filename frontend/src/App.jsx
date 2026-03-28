import { useEffect, useState } from 'react'
import { generatePlan, executePlan } from './api/client'
import FileUpload from './components/FileUpload'
import AgentTimeline from './components/AgentTimeline'
import ReportSummary from './components/ReportSummary'
import IssueCard from './components/IssueCard'
import Sidebar from './components/Sidebar'
import { Bot, Shield, Rocket, CheckCircle, ChevronRight, Menu, X } from 'lucide-react'

const LoadingSteps = ({ step }) => {
  const [agentIndex, setAgentIndex] = useState(0);
  const agents = [
    "Schema Intelligence Agent analyzing structure...",
    "Supervisor Agent routing data packets...",
    "Duplicate Hunter scanning for row clones...",
    "Data Quality Agent auditing null values...",
    "Business Logic Validator checking constraints...",
    "Anomaly Detector performing Z-Score analysis...",
    "Stale Records Agent flagging zombie tasks...",
    "Report Synthesizer finalizing executive summary..."
  ];

  useEffect(() => {
    let interval;
    if (step === "Running AI agents...") {
      interval = setInterval(() => {
        setAgentIndex((prev) => (prev + 1) % agents.length);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step]);

  return (
    <div className="loading-steps glass-panel" style={{ border: '1px solid var(--neon-blue)', boxShadow: '0 0 20px var(--neon-glow)' }}>
      <div className="loader" style={{ borderTopColor: 'var(--neon-blue)' }}></div>
      <div className="loading-text" style={{ minHeight: '1.5em', fontFamily: 'Orbitron', letterSpacing: '1px' }}>
        {step === "Running AI agents..." ? agents[agentIndex] : step}
      </div>
      <div style={{ fontSize: '0.7rem', color: 'var(--neon-blue)', marginTop: '10px', textTransform: 'uppercase', letterSpacing: '2px' }}>
        System Status: {step === "Running AI agents..." ? "ACTIVE_PROCESSING" : "INITIALIZING"}
      </div>
    </div>
  );
};

export default function App() {
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState('')
  const [error, setError] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [plan, setPlan] = useState(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false) // NEW

  const handleUpload = async (selectedFile) => {
    setFile(selectedFile)
    setLoading(true)
    setError(null)
    setReport(null)
    setPlan(null)

    setLoadingStep("Generating Analysis Plan...")
    try {
      const planResult = await generatePlan(selectedFile)
      setPlan(planResult)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleApprovePlan = async () => {
    setLoading(true)
    setLoadingStep("Running AI agents...")
    
    try {
      const result = await executePlan(plan)
      setLoadingStep("Finalizing Report...")
      await new Promise(r => setTimeout(r, 1000))
      setReport(result)
      setPlan(null) // Plan approved and executed
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Derived state for issue list
  const issues = report?.issues || []
  const filteredIssues = issues.filter(issue => {
    const matchSeverity = severityFilter === 'ALL' || issue.severity === severityFilter
    const matchSearch = issue.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                        issue.description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchSeverity && matchSearch
  })

  const severityOrder = { "HIGH": 0, "MEDIUM": 1, "LOW": 2 }
  const sortedIssues = [...filteredIssues].sort((a, b) => 
    (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
  )

  return (
    <>
      <button className="mobile-toggle" onClick={() => setIsSidebarOpen(true)}>
        <Menu size={24} />
      </button>

      <div 
        className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`} 
        onClick={() => setIsSidebarOpen(false)}
      ></div>

      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      <main className="main-content">
        <header className="header-meta">
          <div className="live-status">
            <div className="status-dot"></div>
            LIVE_PROGRESS: {loading ? loadingStep.toUpperCase() : (report ? "SCAN_COMPLETE" : "SYSTEM_READY")}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-grey)' }}>
            ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}
          </div>
        </header>

        <div className="dashboard-container">
          {!plan && !report && !loading && (
            <div className="glass-panel">
              <div className="node-title">
                <Rocket size={18} color="var(--neon-blue)" />
                Initialize New Data Scan
              </div>
              <FileUpload onAnalyze={handleUpload} />
            </div>
          )}
          
          {plan && !loading && (
            <div className="plan-overlay">
              <div className="plan-card">
                <div className="plan-header">
                  <div style={{ color: 'var(--neon-blue)', fontSize: '0.7rem', marginBottom: '5px' }}>SCAN_ROADMAP_GENERATED</div>
                  <h2>Proposed Analysis Plan</h2>
                </div>
                
                <div className="roadmap-list">
                  <div className="roadmap-item">
                    <div className="step-number">1</div>
                    <div>
                      <span className="step-title">Domain Detected</span>
                      <span className="step-desc">Target Environment: {plan.domain.toUpperCase()}</span>
                    </div>
                  </div>
                  <div className="roadmap-item">
                    <div className="step-number">2</div>
                    <div>
                      <span className="step-title">Target Agents ({plan.agents_to_run.length})</span>
                      <span className="step-desc">Deploying: {plan.agents_to_run.join(', ')}</span>
                    </div>
                  </div>
                  <div className="roadmap-item">
                    <div className="step-number">3</div>
                    <div>
                      <span className="step-title">Metadata Extraction</span>
                      <span className="step-desc">Scanning {plan.metadata.rows} rows across {plan.metadata.columns.length} columns</span>
                    </div>
                  </div>
                </div>

                <button className="approve-btn" onClick={handleApprovePlan}>
                  Approve & Execute Scan
                  <ChevronRight size={20} style={{ marginLeft: '10px' }} />
                </button>
                <button 
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-grey)', display: 'block', margin: '15px auto 0', cursor: 'pointer', fontSize: '0.8rem' }}
                  onClick={() => setPlan(null)}
                >
                  Cancel and Reselect File
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="error-container">
              <h3 className="error-title">Analysis Error</h3>
              <div className="error-body">
                {error.includes('validation error') ? (
                  <ul className="error-list">
                    {error.split('  ').filter(l => l.trim().length > 5).map((line, i) => (
                      <li key={i}>{line.trim()}</li>
                    ))}
                  </ul>
                ) : (
                  <p>{error}</p>
                )}
              </div>
              <button className="error-retry-btn" style={{ borderRadius: '8px' }} onClick={() => setError(null)}>Acknowledge & Dismiss</button>
            </div>
          )}

          {loading && <LoadingSteps step={loadingStep} />}

          {report && !loading && (
            <div className="result-view" style={{ animation: 'slideUp 0.5s ease' }}>
              <div className="node-title">
                <Shield size={18} color="var(--neon-blue)" />
                EZYerrScanner Result Summary
              </div>
              <ReportSummary report={report} />
              <AgentTimeline agentStatuses={report.agent_statuses || []} />
              
              <div style={{ marginTop: '3rem' }}>
                <h2 style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border-neon)', paddingBottom: '0.8rem', fontFamily: 'Orbitron', fontSize: '1.2rem' }}>
                  AI System Findings ({sortedIssues.length})
                </h2>
                
                <div className="issue-tabs">
                  {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(level => (
                    <button 
                      key={level}
                      className={`issue-tab ${severityFilter === level ? 'active' : ''}`}
                      onClick={() => setSeverityFilter(level)}
                    >
                      {level === 'ALL' ? 'Total' : level}
                    </button>
                  ))}
                </div>

                <input 
                  type="text" 
                  className="search-input"
                  placeholder="Filter findings by keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'var(--border-neon)' }}
                />

                <div className="issue-list">
                  {sortedIssues.map((issue, idx) => (
                    <IssueCard key={`${issue.title}-${idx}`} issue={issue} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
