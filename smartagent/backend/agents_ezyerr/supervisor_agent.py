import json
from agents_ezyerr.base import BaseAgent
from graph_ezyerr.state import GraphState, Issue

class SupervisorAgent(BaseAgent):
    agent_name = "supervisor"
    
    AVAILABLE_AGENTS = [
        "duplicate_hunter",
        "data_quality", 
        "business_logic",
        "anomaly_detector",
        "stale_records"
    ]

    def analyze(self, state: GraphState) -> list[Issue]:
        return []
    
    def decide_routing(self, state: GraphState) -> list[str]:
        """Uses Gemini to decide which agents to run based on schema."""
        col_types = state.get("column_types", {})
        
        try:
            prompt = f"""
            You are an AI workflow orchestrator. 
            
            Dataset domain: {state.get('domain', 'unknown')}
            Column types detected: {json.dumps(col_types)}
            Has date pairs: {bool(state.get('date_col_pairs'))}
            Has numeric columns: {any(v=='numeric' for v in col_types.values())}
            Has status columns: {any(v=='status' for v in col_types.values())}
            Total rows: {state.get('metadata', {}).get('rows', 0)}
            
            Available agents: {self.AVAILABLE_AGENTS}
            
            Return ONLY a JSON array of agent names to run. 
            Always include duplicate_hunter and data_quality.
            Include business_logic only if there are date columns or amount columns.
            Include anomaly_detector only if there are numeric columns and rows > 20.
            Include stale_records only if there are date AND status columns.
            
            Return ONLY the JSON array, no other text:
            """
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            agents_to_run = json.loads(content)
            return agents_to_run
            
        except Exception as e:
            print(f"SUPERVISOR_AI_ERROR: {e}. Falling back to default routing.")
            # Default fallback routing
            fallback = ["duplicate_hunter", "data_quality"]
            if state.get('date_col_pairs'):
                fallback.append("business_logic")
            if any(v == 'numeric' for v in col_types.values()):
                fallback.append("anomaly_detector")
            return fallback
