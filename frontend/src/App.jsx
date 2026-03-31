import { useState, useEffect } from 'react'
import { generatePlan, executeAnalysisPlan } from './api/client'
import FileUpload from './components/FileUpload'
import AgentTimeline from './components/AgentTimeline'
import ReportSummary from './components/ReportSummary'
import IssueCard from './components/IssueCard'
import Sidebar from './components/Sidebar'
import SmartsheetDashboard from './components/SmartsheetDashboard'
import { Menu } from 'lucide-react'

// ─── File Scanner View ────────────────────────────────────────────────────────
function FileScannerView() {
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  const handleAnalyze = async (file) => {
    setLoading(true); setLoadingMsg('Parsing & Analyzing File...'); setError(null); setReport(null)
    try {
      // 1. Generate Plan
      const plan = await generatePlan(file)
      setLoadingMsg('Running AI specialist agents...')
      
      // 2. Execute Analysis
      const finalReport = await executeAnalysisPlan(plan)
      setReport(finalReport)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredIssues = report?.issues?.filter(iss => 
    iss.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    iss.description?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className="file-scanner-view">
      {!loading && !report && (
        <div style={{ marginTop: '4rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontFamily: 'Orbitron', marginBottom: '0.8rem' }}>
              Deep SCAN <span style={{ color: 'var(--neon-blue)' }}>AI</span>
            </h1>
            <p style={{ color: 'var(--text-grey)', maxWidth: '600px', margin: '0 auto' }}>
              Upload your dataset for a comprehensive multi-agent security and quality audit.
            </p>
          </div>
          <FileUpload onAnalyze={handleAnalyze} />
        </div>
      )}

      {loading && (
        <div className="loading-steps glass-panel" style={{ marginTop: '4rem' }}>
          <div className="loader" />
          <div className="loading-text">{loadingMsg}</div>
        </div>
      )}

      {error && (
        <div className="error-container" style={{ marginTop: '2rem' }}>
          <h3 className="error-title">Analysis Failed</h3>
          <p>{error}</p>
          <button className="error-retry-btn" onClick={() => setError(null)}>Try Again</button>
        </div>
      )}

      {report && (
        <div className="result-view" style={{ animation: 'slideUp 0.5s ease' }}>
          <ReportSummary report={report} />
          <AgentTimeline agentStatuses={report.agent_statuses || []} />
          
          <div style={{ marginTop: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontFamily: 'Orbitron', fontSize: '1.2rem' }}>Audit Findings</h2>
              <input 
                type="text" 
                className="search-input" 
                placeholder="Filter findings..." 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="issue-list">
              {filteredIssues.map((issue, idx) => (
                <IssueCard key={`${issue.title}-${idx}`} issue={issue} />
              ))}
              {filteredIssues.length === 0 && (
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-grey)' }}>
                  No issues found matching your search.
                </div>
              )}
            </div>
          </div>
          
          <button 
            className="approve-btn" 
            style={{ marginTop: '2rem' }}
            onClick={() => setReport(null)}
          >
            Scan Another File
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('file_scan')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <>
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)} 
        activeTab={activeTab} 
        onTabChange={(tab) => {
          setActiveTab(tab)
          setIsSidebarOpen(false)
        }} 
      />

      <div className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`} onClick={() => setIsSidebarOpen(false)} />

      <main className="main-content">
        <header className="header-meta mobile-only-header" style={{ marginBottom: '1.5rem' }}>
          <button className="mobile-toggle" onClick={() => setIsSidebarOpen(true)} style={{ position: 'static', margin: 0 }}>
            <Menu size={20} />
          </button>
          <div className="live-status" style={{ marginLeft: 'auto' }}>
            <div className="status-dot" />
            SYSTEM_ACTIVE: {activeTab.toUpperCase()}
          </div>
        </header>

        {activeTab === 'file_scan' && <FileScannerView />}
        {activeTab === 'smartsheet_audit' && <SmartsheetDashboard />}
        {activeTab === 'settings' && (
          <div className="glass-panel" style={{ marginTop: '2rem', padding: '3rem' }}>
            <h2 style={{ fontFamily: 'Orbitron', marginBottom: '1rem' }}>Settings</h2>
            <p style={{ color: 'var(--text-grey)' }}>System configuration and API keys management coming soon.</p>
          </div>
        )}
      </main>
    </>
  )
}
