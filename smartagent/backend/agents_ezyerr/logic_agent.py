import pandas as pd
import json
from agents_ezyerr.base import BaseAgent
from graph_ezyerr.state import GraphState, Issue

class BusinessLogicAgent(BaseAgent):
    agent_name = "business_logic"
    
    def analyze(self, state: GraphState) -> list[Issue]:
        df = self._get_dataframe(state)
        findings = []
        
        # a) Date pair violations
        date_pairs = state.get("date_col_pairs", [])
        for start_col, end_col in date_pairs:
            if start_col in df.columns and end_col in df.columns:
                try:
                    s = pd.to_datetime(df[start_col], errors='coerce')
                    e = pd.to_datetime(df[end_col], errors='coerce')
                    invalid_mask = e <= s
                    if invalid_mask.any():
                        affected = df[invalid_mask].index.tolist()
                        findings.append({
                            "type": "date_pair_violation",
                            "columns": [start_col, end_col],
                            "count": len(affected),
                            "affected_rows": affected[:100]
                        })
                except Exception: pass

        # b) Invalid date formats
        # skipping deep format checks for brevity, relying on NaT coercion density
        
        # c) Negative amounts
        amt_cols = [c for c in df.columns if any(x in c.lower() for x in ['price','budget','cost','amount','salary'])]
        for col in amt_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                neg = df[df[col] < 0]
                if len(neg) > 0:
                    findings.append({
                        "type": "negative_amount", "column": col, "count": len(neg),
                        "affected_rows": neg.index.tolist()[:100]
                    })

        # d) Over-budget
        if "actual_cost" in df.columns and "budget" in df.columns:
            if pd.api.types.is_numeric_dtype(df["actual_cost"]) and pd.api.types.is_numeric_dtype(df["budget"]):
                over = df[df["actual_cost"] > df["budget"]]
                if len(over) > 0:
                    findings.append({
                        "type": "over_budget", "columns": ["actual_cost", "budget"], "count": len(over),
                        "affected_rows": over.index.tolist()[:100]
                    })

        # f) Cross-column status inconsistency
        status_cols = [c for c, t in state.get('column_types', {}).items() if t=='status' and c in df.columns]
        pct_cols = [c for c in df.columns if 'pct' in c.lower() or 'percent' in c.lower()]
        if status_cols and pct_cols:
            s_col = status_cols[0]
            p_col = pct_cols[0]
            try:
                mask = df[s_col].astype(str).str.lower().isin(['done', 'completed']) & (df[p_col] < 100)
                if mask.any():
                    affected = df[mask].index.tolist()
                    findings.append({
                        "type": "status_pct_mismatch", "columns": [s_col, p_col], "count": len(affected),
                        "affected_rows": affected[:100]
                    })
            except Exception: pass

        if not findings: return []
        return self._enrich_findings(findings, state)
        
    def _enrich_findings(self, findings, state):
        prompt = f"""
        You are a business process expert for {state.get('domain', 'generic')}.
        These are rule violations that indicate broken business processes: {json.dumps(findings, default=str)}
        
        Describe the BUSINESS impact of each violation (what could go wrong in real operations)
        and give specific corrective actions.
        
        For EACH finding, return a JSON array of issue objects. Each object must have:
        - "title": short issue name
        - "description": business impact description
        - "severity": "HIGH", "MEDIUM", or "LOW" based on rule severity (date pairs=HIGH, negative amount=HIGH)
        - "suggested_fix": corrective action
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
                description=enrich.get("description", f"Logic failure: {finding}"),
                severity=enrich.get("severity", "MEDIUM"),
                rows=finding.get("affected_rows", []),
                cols=finding.get("columns", [finding.get("column")] if finding.get("column") else []),
                fix=enrich.get("suggested_fix", "Fix logic inconsistency."),
                count=finding.get("count", 0),
                confidence=enrich.get("confidence", 0.9)
            ))
        return issues
