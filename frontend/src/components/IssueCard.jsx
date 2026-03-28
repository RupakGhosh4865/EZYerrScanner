import { useState } from 'react';
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react';

export const SeverityBadge = ({ severity }) => {
  const map = {
    'HIGH': { bg: 'rgba(239, 68, 68, 0.2)', color: 'var(--red)', border: 'rgba(239, 68, 68, 0.4)' },
    'MEDIUM': { bg: 'rgba(245, 158, 11, 0.2)', color: 'var(--amber)', border: 'rgba(245, 158, 11, 0.4)' },
    'LOW': { bg: 'rgba(100, 116, 139, 0.2)', color: 'var(--gray)', border: 'rgba(100, 116, 139, 0.4)' },
  };
  const theme = map[severity] || map['LOW'];
  
  return (
    <span className="severity-badge" style={{ backgroundColor: theme.bg, color: theme.color, borderColor: theme.border }}>
      {severity}
    </span>
  );
};

export default function IssueCard({ issue }) {
  const [open, setOpen] = useState(false);
  const severityClass = issue.severity ? issue.severity.toLowerCase() : 'low';
  
  const affectedRows = issue.affected_rows || [];
  const displayRows = affectedRows.slice(0, 5);
  const rowCount = issue.count || affectedRows.length || 0;
  
  return (
    <div className={`issue-card ${severityClass}`}>
      <div className="issue-header">
        <h4 className="issue-title">
          <SeverityBadge severity={issue.severity || 'LOW'} />
          {issue.title}
        </h4>
        <span className="agent-badge">Agent: {issue.agent}</span>
      </div>
      
      <p className="issue-desc">{issue.description}</p>
      
      <button className="details-toggle" onClick={() => setOpen(!open)}>
        {open ? <><ChevronUp size={16} style={{display:'inline', verticalAlign: 'middle'}}/> Hide details</> : <><ChevronDown size={16} style={{display:'inline', verticalAlign: 'middle'}}/> Show tech details</>}
      </button>

      {open && (
        <div className="issue-details">
          {issue.affected_columns && issue.affected_columns.length > 0 && (
            <div>
              <strong>Columns Flagged:</strong>
              <div className="pill-list">
                {issue.affected_columns.map(c => <span key={c} className="pill">{c}</span>)}
              </div>
            </div>
          )}
          
          <div style={{ marginTop: '0.5rem' }}>
            <strong>Affected Rows:</strong> {displayRows.join(', ')} 
            {rowCount > 5 ? ` (+${rowCount - 5} more)` : ''} 
            {displayRows.length === 0 && ' (Dataset wide)'}
          </div>
          
          {issue.suggested_fix && (
            <div className="fix-box">
              <Wrench size={20} />
              <div>
                <strong style={{ display: 'block', color: 'var(--green)', letterSpacing: '0.5px', textTransform: 'uppercase', fontSize:'0.8rem', marginBottom: '0.25rem' }}>Automated Fix Suggestion</strong>
                {issue.suggested_fix}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
