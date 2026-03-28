import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Activity, Share2 } from 'lucide-react';

const friendlyNames = {
  "schema_intelligence": "Schema AI",
  "supervisor": "Orchestrator",
  "duplicate_hunter": "Duplicate Scan",
  "data_quality": "Quality Check",
  "business_logic": "Logic Validator",
  "anomaly_detector": "Anomaly AI",
  "stale_records": "Stale Detector",
  "report_synthesizer": "AI Summarizer"
};

const getStatusIcon = (status, issueCount) => {
  if (status === 'skipped') return <XCircle size={14} />;
  if (status === 'done' && issueCount === 0) return <CheckCircle2 size={14} color="var(--green)" />;
  if (status === 'done' && issueCount > 0) return <AlertTriangle size={14} color="var(--amber)" />;
  return <Activity size={14} color="var(--neon-blue)" className="animate-pulse" />;
};

const AgentNode = ({ name, stat, x, y }) => {
  const { status, issue_count } = stat || { status: 'pending', issue_count: 0 };
  const icon = getStatusIcon(status, issue_count);
  const title = friendlyNames[name] || name;

  return (
    <div 
      className={`graph-node ${status}`}
      style={{ 
        position: 'absolute', 
        left: `${x}%`, 
        top: `${y}%`,
        transform: 'translate(-50%, -50%)'
      }}
    >
      <div className="node-wrapper">
        <div className="node-ring"></div>
        <div className="node-core">
          {icon}
        </div>
        <div className="node-label-container">
          <span className="node-name">{title}</span>
          {status === 'done' && <span className="node-status-msg">COMPLETE</span>}
        </div>
      </div>
      {issue_count > 0 && <div className="node-issues-count">{issue_count}</div>}
    </div>
  );
};

export default function AgentTimeline({ agentStatuses = [] }) {
  const findStat = (name) => agentStatuses.find(a => a.name === name);

  // Position definitions for nodes (percentage based)
  const nodes = [
    { name: 'schema_intelligence', x: 10, y: 50 },
    { name: 'supervisor', x: 30, y: 50 },
    { name: 'duplicate_hunter', x: 55, y: 15 },
    { name: 'data_quality', x: 60, y: 32 },
    { name: 'business_logic', x: 65, y: 50 },
    { name: 'anomaly_detector', x: 60, y: 68 },
    { name: 'stale_records', x: 55, y: 85 },
    { name: 'report_synthesizer', x: 85, y: 50 }
  ];

  return (
    <div className="neural-graph-container glass-panel">
      <div className="node-title">
        <Share2 size={18} color="var(--neon-blue)" />
        Neural Agent Interaction Matrix
      </div>
      
      <div className="neural-canvas">
        <svg className="neural-svg" viewBox="0 0 1000 400" preserveAspectRatio="xMidYMid meet">
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Connection Paths */}
          {/* Start to Supervisor */}
          <path d="M 100 200 L 300 200" className={`conn-path ${findStat('schema_intelligence')?.status === 'done' ? 'active' : ''}`} />
          
          {/* Supervisor to Specialists */}
          <path d="M 300 200 Q 400 200, 550 60" className={`conn-path ${findStat('supervisor')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 300 200 Q 400 200, 600 128" className={`conn-path ${findStat('supervisor')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 300 200 L 650 200" className={`conn-path ${findStat('supervisor')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 300 200 Q 400 200, 600 272" className={`conn-path ${findStat('supervisor')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 300 200 Q 400 200, 550 340" className={`conn-path ${findStat('supervisor')?.status === 'done' ? 'active' : ''}`} />

          {/* Specialists to Synthesizer */}
          <path d="M 550 60 Q 750 200, 850 200" className={`conn-path ${findStat('duplicate_hunter')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 600 128 Q 750 200, 850 200" className={`conn-path ${findStat('data_quality')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 650 200 L 850 200" className={`conn-path ${findStat('business_logic')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 600 272 Q 750 200, 850 200" className={`conn-path ${findStat('anomaly_detector')?.status === 'done' ? 'active' : ''}`} />
          <path d="M 550 340 Q 750 200, 850 200" className={`conn-path ${findStat('stale_records')?.status === 'done' ? 'active' : ''}`} />
        </svg>

        <div className="nodes-overlay">
          {nodes.map(node => (
            <AgentNode 
              key={node.name} 
              name={node.name} 
              stat={findStat(node.name)} 
              x={node.x} 
              y={node.y} 
            />
          ))}
        </div>
      </div>

      <style jsx>{`
        .neural-graph-container {
          margin-top: 3rem;
          padding: 2.5rem;
          min-height: 500px;
          display: flex;
          flex-direction: column;
        }

        .neural-canvas {
          flex: 1;
          position: relative;
          width: 100%;
          min-height: 400px;
        }

        .neural-svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }

        .conn-path {
          fill: none;
          stroke: rgba(0, 242, 254, 0.05);
          stroke-width: 2;
          transition: stroke 1s, stroke-width 1s;
        }

        .conn-path.active {
          stroke: var(--neon-blue);
          stroke-dasharray: 10, 5;
          animation: flow 20s linear infinite;
          opacity: 0.6;
          filter: url(#glow);
        }

        @keyframes flow {
          from { stroke-dashoffset: 200; }
          to { stroke-dashoffset: 0; }
        }

        .nodes-overlay {
          position: absolute;
          inset: 0;
          pointer-events: none;
        }

        .graph-node {
          width: 100px;
          height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
          pointer-events: auto;
        }

        .node-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
        }

        .node-ring {
          position: absolute;
          width: 44px;
          height: 44px;
          border: 1px solid rgba(0, 242, 254, 0.2);
          border-radius: 50%;
          transition: all 0.5s;
        }

        .graph-node.active .node-ring {
          border-color: var(--neon-blue);
          box-shadow: 0 0 15px var(--neon-glow);
          transform: scale(1.2);
          animation: pulseNode 1.5s infinite;
        }

        .graph-node.done .node-ring {
          border-color: var(--green);
          background: rgba(34, 197, 94, 0.05);
        }

        .node-core {
          width: 36px;
          height: 36px;
          background: var(--bg-dark);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 5;
        }

        .node-label-container {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .node-name {
          font-family: var(--font-header);
          font-size: 0.65rem;
          font-weight: 600;
          color: var(--text-grey);
          text-transform: uppercase;
          letter-spacing: 1px;
          white-space: nowrap;
        }

        .node-status-msg {
          font-size: 0.5rem;
          color: var(--green);
          font-weight: 800;
          letter-spacing: 1px;
        }

        .graph-node.done .node-name { color: #fff; }
        .graph-node.active .node-name { color: var(--neon-blue); }

        .node-issues-count {
          position: absolute;
          top: 15px;
          right: 15px;
          background: var(--amber);
          color: #000;
          font-size: 0.6rem;
          font-weight: 800;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 10px var(--amber-glow);
        }

        @keyframes pulseNode {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.3); opacity: 0.5; }
          100% { transform: scale(1); opacity: 1; }
        }

        .animate-pulse {
          animation: iconPulse 2s infinite;
        }

        @keyframes iconPulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.7; }
        }
      `}</style>
    </div>
  );
}
