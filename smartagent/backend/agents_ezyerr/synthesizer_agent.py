import json
from agents_ezyerr.base import BaseAgent
from graph_ezyerr.state import GraphState

class ReportSynthesizerAgent(BaseAgent):
    agent_name = "report_synthesizer"
    
    def analyze(self, state: GraphState) -> list:
        return []
    
    def synthesize(self, state: GraphState) -> dict:
        issues = state.get("issues", [])
        if not issues:
            return {
                "health_score": 100,
                "executive_summary": "No issues detected. Dataset appears clean.",
                "top_priorities": []
            }
        
        # Calculate health score BEFORE calling Gemini (deterministic)
        health_score = 100
        high_count = sum(1 for i in issues if i["severity"] == "HIGH")
        med_count = sum(1 for i in issues if i["severity"] == "MEDIUM")
        low_count = sum(1 for i in issues if i["severity"] == "LOW")
        health_score -= min(high_count * 12, 55)
        health_score -= min(med_count * 6, 30)
        health_score -= min(low_count * 2, 15)
        health_score = max(0, health_score)
        
        # Sort issues by severity for the prompt
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x["severity"], 3))
        
        # Build compact issue summary for Gemini (avoid token waste)
        issue_summary = []
        for issue in sorted_issues[:20]:  # Cap at 20 to manage tokens
            issue_summary.append({
                "agent": issue.get("agent", "unknown"),
                "title": issue.get("title", ""),
                "severity": issue.get("severity", "LOW"),
                "count": issue.get("count", 0),
                "description": issue.get("description", "")[:150]  # Truncate for tokens
            })
        
        agents_run = state.get("agents_to_run", [])
        
        prompt = f"""
        You are a Chief Data Officer preparing an executive briefing.
        
        Dataset: {state.get('metadata', {}).get('filename', 'Unknown')} 
        Domain: {state.get('domain', 'generic')}
        Rows: {state.get('metadata', {}).get('rows', 0)} | Columns: {len(state.get('metadata', {}).get('columns', []))}
        Data Health Score: {health_score}/100
        Total Issues Found: {len(issues)} 
        (HIGH: {high_count}, MEDIUM: {med_count}, LOW: {low_count})
        
        Issues detected:
        {json.dumps(issue_summary, indent=2)}
        
        Agents that ran: {', '.join(agents_run)}
        
        Return ONLY this JSON structure, no other text:
        {{
          "executive_summary": "3-4 sentence summary. Start with health score context. Call out the most critical finding. End with overall recommendation.",
          "top_priorities": [
            "Priority 1: [Agent] - [specific action to take first]",
            "Priority 2: [Agent] - [specific action to take second]",  
            "Priority 3: [Agent] - [specific action to take third]"
          ],
          "risk_level": "CRITICAL|HIGH|MODERATE|LOW",
          "estimated_fix_time": "e.g., 2-4 hours of data cleaning"
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"): content = content[7:-3]
            elif content.startswith("```"): content = content[3:-3]
            result = json.loads(content)
        except Exception as e:
            print(f"[{self.agent_name}] LLM synthesis failed: {e}")
            result = {
                "executive_summary": "Synthesis failed due to API limits. Manual review required.",
                "top_priorities": ["Priority 1: Check issues tab manually.", "Priority 2: Provide valid API Key."],
                "risk_level": "UNKNOWN",
                "estimated_fix_time": "Unknown"
            }
        
        return {
            "health_score": health_score,
            "executive_summary": result.get("executive_summary", ""),
            "top_priorities": result.get("top_priorities", []),
        }
