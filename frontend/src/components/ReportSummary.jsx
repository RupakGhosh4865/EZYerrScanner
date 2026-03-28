import { useState, useEffect } from 'react';

export default function ReportSummary({ report }) {
  const [healthScore, setHealthScore] = useState(0);
  
  useEffect(() => {
    // Animate health score from 0 up to actual on mount
    const timer = setTimeout(() => {
      setHealthScore(report.health_score || 0);
    }, 100);
    return () => clearTimeout(timer);
  }, [report.health_score]);

  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (healthScore / 100) * circumference;
  
  const getColor = (score) => {
    if (score >= 80) return 'var(--green)';
    if (score >= 50) return 'var(--amber)';
    return 'var(--red)';
  };

  const domainMap = {
    'generic': 'Generic',
    'project_management': 'Project Management',
    'hr': 'Human Resources',
    'finance': 'Finance'
  };

  const totals = report.total_issues_by_severity || { HIGH: 0, MEDIUM: 0, LOW: 0 };
  const numIssues = report.issues ? report.issues.length : 0;
  
  const agentsRunCount = Array.isArray(report.agent_statuses) 
    ? report.agent_statuses.filter(a => a.status === 'done' && a.duration_ms > 0).length 
    : 0;

  return (
    <div className="report-summary-box">
      <div style={{ textAlign: 'center', borderRight: '1px solid var(--border)', paddingRight: '2rem' }}>
        <div className="health-score-container">
          <svg className="health-score-svg" viewBox="0 0 160 160">
            <circle cx="80" cy="80" r={radius} className="health-score-bg" />
            <circle cx="80" cy="80" r={radius} className="health-score-fill"
              style={{
                stroke: getColor(healthScore),
                strokeDashoffset,
                strokeDasharray: circumference
              }}
            />
          </svg>
          <div className="health-score-text">
            <div className="health-score-value" style={{ color: getColor(healthScore) }}>{healthScore}</div>
            <div className="health-score-label">Health Score</div>
          </div>
        </div>
        <div className="domain-badge">
          Domain: {domainMap[report.domain] || report.domain}
        </div>
        
        <div className="stat-grid">
          <div className="stat-box">
            <div className="stat-box-value">{report.metadata?.rows || 0}</div>
            <div className="stat-box-label">Rows Scanned</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-value">{numIssues}</div>
            <div className="stat-box-label">Total Issues</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-value text-high">{totals.HIGH || 0}</div>
            <div className="stat-box-label">Critical Risks</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-value">{agentsRunCount}</div>
            <div className="stat-box-label">Agents Ran</div>
          </div>
        </div>
      </div>

      <div className="report-content" style={{ paddingLeft: '1rem' }}>
        <h3>Executive Summary</h3>
        <div className="exec-summary-card">
          {report.executive_summary || "Synthesis complete. No summary generated."}
        </div>
        
        <h3 className="priority-title">Top Priorities</h3>
        <ul className="priority-list">
          {(report.top_priorities && report.top_priorities.length > 0) ? (
            report.top_priorities.map((task, i) => (
              <li key={i}>
                <strong>{i+1}.</strong> {task}
              </li>
            ))
          ) : (
            <li>No priority actions designated.</li>
          )}
        </ul>

        {numIssues > 0 && (
          <div className="issue-breakdown-bar">
            {(totals.HIGH > 0) && <div className="bar-segment" style={{ width: `${(totals.HIGH / numIssues) * 100}%`, background: 'var(--red)' }} />}
            {(totals.MEDIUM > 0) && <div className="bar-segment" style={{ width: `${(totals.MEDIUM / numIssues) * 100}%`, background: 'var(--amber)' }} />}
            {(totals.LOW > 0) && <div className="bar-segment" style={{ width: `${(totals.LOW / numIssues) * 100}%`, background: 'var(--gray)' }} />}
          </div>
        )}
      </div>
    </div>
  );
}
