import json
from fuzzywuzzy import fuzz
from .base import BaseAgent
from ..graph.state import GraphState, Issue

class DuplicateHunterAgent(BaseAgent):
    agent_name = "duplicate_hunter"
    
    def analyze(self, state: GraphState) -> list[Issue]:
        df = self._get_dataframe(state)
        findings = []
        
        # CHECK 1: Exact duplicate rows
        exact_dupes = df[df.duplicated(keep=False)]
        if len(exact_dupes) > 0:
            findings.append({
                "type": "exact_duplicates",
                "affected_rows": exact_dupes.index.tolist(),
                "count": len(exact_dupes) // 2,
                "sample": exact_dupes.head(2).to_dict('records')
            })
        
        # CHECK 2: Duplicate primary keys
        pk_cols = state.get("primary_key_cols", [])
        if pk_cols:
            pk_cols_valid = [c for c in pk_cols if c in df.columns]
            if pk_cols_valid:
                pk_dupes = df[df.duplicated(subset=pk_cols_valid, keep=False)]
                if len(pk_dupes) > 0:
                    findings.append({
                        "type": "duplicate_primary_keys",
                        "columns": pk_cols_valid,
                        "affected_rows": pk_dupes.index.tolist(),
                        "count": len(pk_dupes),
                        "sample": pk_dupes.head(3).to_dict('records')
                    })
        
        # CHECK 3: Near-duplicate names
        text_cols = [c for c,t in state.get("column_types",{}).items() 
                     if t in ("name","text") and c in df.columns]
        for col in text_cols[:2]:  # Max 2 text columns
            values = df[col].dropna().astype(str).tolist()
            indices = df[col].dropna().index.tolist()
            near_dupe_pairs = []
            max_len = min(len(values), 100)
            for i in range(max_len):
                for j in range(i+1, max_len):
                    score = fuzz.ratio(values[i].lower(), values[j].lower())
                    if 88 <= score < 100:
                        near_dupe_pairs.append((indices[i], indices[j], values[i], values[j], score))
            if near_dupe_pairs:
                affected = list(set([p[0] for p in near_dupe_pairs] + [p[1] for p in near_dupe_pairs]))
                findings.append({
                    "type": "near_duplicates",
                    "column": col,
                    "affected_rows": affected,
                    "pairs": near_dupe_pairs[:5],
                    "count": len(near_dupe_pairs)
                })
        
        if not findings:
            return []
            
        return self._enrich_findings(findings, state)
        
    def _enrich_findings(self, findings, state):
        prompt = f"""
        You are a data quality expert. I found these duplicate issues in a {state.get('domain', 'generic')} dataset.
        
        Findings: {json.dumps(findings, default=str)}
        Dataset size: {state.get('metadata', {}).get('rows', len(self._get_dataframe(state)))} rows
        
        For EACH finding, return a JSON array of issue objects. Each object must have:
        - "title": short issue name (max 8 words)
        - "description": plain English explanation of the problem and its impact (2 sentences)
        - "severity": "HIGH" if >5% of data affected, else "MEDIUM"
        - "suggested_fix": specific actionable fix with exact steps (2-3 sentences)
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
                description=enrich.get("description", f"Raw finding: {finding}"),
                severity=enrich.get("severity", "MEDIUM"),
                rows=finding.get("affected_rows", []),
                cols=finding.get("columns", [finding.get("column")] if finding.get("column") else []),
                fix=enrich.get("suggested_fix", "Manual review needed."),
                count=finding.get("count", 0),
                confidence=enrich.get("confidence", 0.8)
            ))
        return issues
