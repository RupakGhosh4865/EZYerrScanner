import pandas as pd
import numpy as np
from scipy import stats
import json
from agents_ezyerr.base import BaseAgent
from graph_ezyerr.state import GraphState, Issue

class AnomalyDetectorAgent(BaseAgent):
    agent_name = "anomaly_detector"
    
    def analyze(self, state: GraphState) -> list[Issue]:
        df = self._get_dataframe(state)
        findings = []
        
        for col in df.select_dtypes(include=[np.number]).columns:
            col_data = df[col].dropna()
            if len(col_data) < 10: continue
            
            # a & b) Z-score & IQR Outliers
            z_scores = np.abs(stats.zscore(col_data))
            q1, q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            iqr = q3 - q1
            z_outliers = col_data[z_scores > 2.5].index
            iqr_outliers = col_data[(col_data < q1 - 1.5*iqr) | (col_data > q3 + 1.5*iqr)].index
            union_outliers = list(set(z_outliers) | set(iqr_outliers))
            
            if union_outliers:
                max_z = z_scores.max() if len(z_scores) > 0 else 0
                findings.append({
                    "type": "outliers", "column": col, "count": len(union_outliers),
                    "severity_guess": "HIGH" if max_z > 4.0 else "MEDIUM",
                    "affected_rows": union_outliers[:100]
                })
                
            # e) Skewness
            skew_val = stats.skew(col_data)
            if abs(skew_val) > 3.0:
                findings.append({
                    "type": "distribution_skew", "column": col, "skewness": skew_val,
                    "count": len(col_data)
                })
                
            # d) Impossible values
            if any(x in col.lower() for x in ['age','years','count','quantity','hours','days','score','rating']):
                neg_vals = col_data[col_data < 0]
                if len(neg_vals) > 0:
                    findings.append({
                        "type": "impossible_negative", "column": col, "count": len(neg_vals),
                        "affected_rows": neg_vals.index.tolist()[:100]
                    })

        if not findings: return []
        return self._enrich_findings(findings, state)
        
    def _enrich_findings(self, findings, state):
        prompt = f"""
        You are a statistical analyst. These are anomalies detected in {state.get('domain', 'generic')} data using z-score and IQR methods: {json.dumps(findings, default=str)}
        
        For each anomaly cluster, explain in plain English: what the anomaly likely represents (data entry error? fraud? system glitch?), and what investigation steps to take.
        
        For EACH finding, return a JSON array of issue objects. Each object must have:
        - "title": short issue name
        - "description": statistical context and likely real-world cause
        - "severity": "HIGH", "MEDIUM", or "LOW"
        - "suggested_fix": investigation steps
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
                description=enrich.get("description", f"Statistical anomaly: {finding}"),
                severity=enrich.get("severity", finding.get("severity_guess", "MEDIUM")),
                rows=finding.get("affected_rows", []),
                cols=[finding["column"]] if "column" in finding else [],
                fix=enrich.get("suggested_fix", "Review outlier distribution."),
                count=finding.get("count", 0),
                confidence=enrich.get("confidence", 0.7)
            ))
        return issues
