import pandas as pd
import json
from agents.base import BaseAgent
from graph.state import GraphState, Issue

class DataQualityAgent(BaseAgent):
    agent_name = "data_quality"
    
    def analyze(self, state: GraphState) -> list[Issue]:
        df = self._get_dataframe(state)
        findings = []
        rows = len(df)
        if rows == 0: return []
            
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            if null_count == 0: continue
            null_pct = null_count / rows
            if null_pct == 1.0:
                severity = "HIGH"
                desc = "Completely empty column"
            elif null_pct > 0.5:
                severity = "HIGH"
                desc = ">50% nulls"
            elif null_pct > 0.2:
                severity = "MEDIUM"
                desc = "20-50% nulls"
            elif null_pct > 0.05:
                severity = "LOW"
                desc = "5-20% nulls"
            else: continue
            findings.append({
                "type": "null_values", "column": col, "null_count": null_count,
                "null_pct": round(null_pct*100, 2), "severity": severity, "desc": desc,
                "affected_rows": df[df[col].isnull()].index.tolist()[:100]
            })

        for col in df.columns:
            types = df[col].dropna().apply(type).unique()
            if len(types) > 1:
                findings.append({
                    "type": "type_inconsistency", "column": col,
                    "types_found": [str(t) for t in types],
                    "count": len(df[col].dropna()),
                    "affected_rows": df[col].dropna().index.tolist()[:50]
                })

        col_types = state.get("column_types", {})
        status_cols = [c for c, t in col_types.items() if t == "status" and c in df.columns]
        for col in status_cols:
            vals = df[col].dropna().astype(str)
            lower_vals = vals.str.lower()
            for val, _ in lower_vals.value_counts().items():
                actuals = vals[lower_vals == val].unique()
                if len(actuals) > 1:
                    affected = vals[vals.isin(actuals)].index.tolist()
                    findings.append({
                        "type": "inconsistent_casing", "column": col,
                        "variations": actuals.tolist(), "count": len(affected),
                        "affected_rows": affected[:100]
                    })
        
        pct_cols = [c for c in df.columns if "pct" in c.lower() or "percent" in c.lower() or col_types.get(c) == "percentage"]
        for col in pct_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                invalid = df[(df[col] > 100) | (df[col] < 0)]
                if len(invalid) > 0:
                    findings.append({
                        "type": "invalid_percentage", "column": col,
                        "count": len(invalid), "affected_rows": invalid.index.tolist()
                    })

        if not findings: return []
            
        return self._enrich_findings(findings, state)
        
    def _enrich_findings(self, findings, state):
        prompt = f"""
        You are a data quality expert for a {state.get('domain', 'generic')} dataset.
        Here are the data quality findings: {json.dumps(findings, default=str)}
        
        For EACH finding, return a JSON array of issue objects. Each object must meet:
        - "title": short issue name
        - "description": clear business-impact description explaining WHY this matters
        - "severity": "HIGH", "MEDIUM", or "LOW"
        - "suggested_fix": specific actionable fix steps
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
                description=enrich.get("description", finding.get("desc", f"Raw: {finding}")),
                severity=enrich.get("severity", finding.get("severity", "MEDIUM")),
                rows=finding.get("affected_rows", []),
                cols=[finding["column"]] if "column" in finding else [],
                fix=enrich.get("suggested_fix", "Review quality issue."),
                count=finding.get("count", finding.get("null_count", 0)),
                confidence=enrich.get("confidence", 0.8)
            ))
        return issues
