import pandas as pd
import json
from .base import BaseAgent
from ..graph.state import GraphState, Issue

class StaleRecordsAgent(BaseAgent):
    agent_name = "stale_records"
    
    def analyze(self, state: GraphState) -> list[Issue]:
        df = self._get_dataframe(state)
        findings = []
        today = pd.Timestamp.now().normalize()
        done_statuses = ["done", "completed", "closed", "resolved"]
        
        status_cols = [c for c, t in state.get('column_types', {}).items() if t == "status" and c in df.columns]
        s_col = status_cols[0] if status_cols else None
        
        # a) Overdue tasks & d) Missing deadlines
        due_col = next((c for c in df.columns if any(x in c.lower() for x in ['due', 'deadline'])), None)
        if due_col:
            dates = pd.to_datetime(df[due_col], errors='coerce')
            missing = dates.isnull()
            if len(dates.dropna()) / len(df) > 0.8 and missing.sum() > 0:
                findings.append({
                    "type": "missing_deadline", "count": int(missing.sum()),
                    "affected_rows": df[missing].index.tolist()[:100]
                })

            if s_col:
                not_done = ~df[s_col].astype(str).str.lower().isin(done_statuses)
                overdue = df[not_done & (dates < today)]
                if len(overdue) > 0:
                    findings.append({
                        "type": "overdue_tasks", "count": len(overdue),
                        "affected_rows": overdue.index.tolist()[:100]
                    })

        # b) Zombie records
        up_col = next((c for c in df.columns if any(x in c.lower() for x in ['update', 'modified'])), None)
        if up_col and s_col:
            udates = pd.to_datetime(df[up_col], errors='coerce')
            not_done = ~df[s_col].astype(str).str.lower().isin(done_statuses)
            zombie = df[not_done & (udates < today - pd.Timedelta(days=60))]
            if len(zombie) > 0:
                findings.append({
                    "type": "zombie_records", "count": len(zombie),
                    "affected_rows": zombie.index.tolist()[:100]
                })

        # c) Future dates with past status & e) Long-running
        start_col = next((c for c in df.columns if 'start' in c.lower()), None)
        if start_col and s_col:
            sdates = pd.to_datetime(df[start_col], errors='coerce')
            is_done = df[s_col].astype(str).str.lower().isin(done_statuses)
            future_done = df[is_done & (sdates > today)]
            if len(future_done) > 0:
                findings.append({
                    "type": "future_start_done", "count": len(future_done),
                    "affected_rows": future_done.index.tolist()[:100]
                })
                
            not_done = ~df[s_col].astype(str).str.lower().isin(done_statuses)
            long_running = df[not_done & (sdates < today - pd.Timedelta(days=90))]
            if len(long_running) > 0:
                findings.append({
                    "type": "long_running_tasks", "count": len(long_running),
                    "affected_rows": long_running.index.tolist()[:100]
                })

        if not findings: return []
        return self._enrich_findings(findings, state)
        
    def _enrich_findings(self, findings, state):
        prompt = f"""
        You are a project management consultant analyzing {state.get('domain', 'generic')} data.
        These are stale and overdue records that represent operational risk: {json.dumps(findings, default=str)}
        
        For each finding, write an urgent, action-oriented description that a project manager can act on today. Include timeline urgency.
        
        For EACH finding, return a JSON array of issue objects. Each object must have:
        - "title": short issue name
        - "description": urgent operational business impact
        - "severity": "HIGH", "MEDIUM", or "LOW" based on risk rules
        - "suggested_fix": corrective action for a PM
        - "confidence": float 0.0-1.0
        
        Return ONLY the JSON array. No markdown, no preamble.
        """
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"): content = content[7:-3]
            elif content.startswith("```"): content = content[3:-3]
            enrichments = json.loads(content)
        except Exception as e:
            print(f"[{self.agent_name}] LLM enrichment failed: {e}")
            enrichments = [{}] * len(findings)

        issues = []
        for i, finding in enumerate(findings):
            enrich = enrichments[i] if isinstance(enrichments, list) and i < len(enrichments) else {}
            issues.append(self._create_issue(
                title=enrich.get("title", f"System: {finding['type']}"),
                description=enrich.get("description", f"Stale check: {finding}"),
                severity=enrich.get("severity", "MEDIUM"),
                rows=finding.get("affected_rows", []),
                cols=[c for c in ["due", "start", "update"] if c in finding.get("type", "")] ,
                fix=enrich.get("suggested_fix", "Review record status."),
                count=finding.get("count", 0),
                confidence=enrich.get("confidence", 0.85)
            ))
        return issues
