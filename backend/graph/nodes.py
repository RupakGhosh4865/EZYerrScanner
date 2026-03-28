import time
from .state import GraphState, AgentStatus
from ..agents.schema_agent import SchemaIntelligenceAgent
from ..agents.supervisor_agent import SupervisorAgent
from ..agents.duplicate_agent import DuplicateHunterAgent
from ..agents.quality_agent import DataQualityAgent
from ..agents.logic_agent import BusinessLogicAgent
from ..agents.anomaly_agent import AnomalyDetectorAgent
from ..agents.stale_agent import StaleRecordsAgent
from ..agents.synthesizer_agent import ReportSynthesizerAgent
from ..services.file_parser import parse_file
from datetime import datetime

def _run_agent(agent_cls, state: GraphState) -> dict:
    agent = agent_cls()
    if state.get("agents_to_run") and agent.agent_name not in state["agents_to_run"]:
        return {"agent_statuses": [{"name": agent.agent_name, "status": "skipped", "duration_ms": 0, "issue_count": 0}]}
        
    start_time = time.time()
    try:
        issues = agent.analyze(state)
        status = "done"
    except Exception as e:
        print(f"Error in {agent.agent_name}: {e}")
        issues = []
        status = "failed"
        
    duration = int((time.time() - start_time) * 1000)
    return {
        "issues": issues,
        "agent_statuses": [{"name": agent.agent_name, "status": status, "duration_ms": duration, "issue_count": len(issues)}]
    }

def duplicate_node(state: GraphState) -> dict: return _run_agent(DuplicateHunterAgent, state)
def quality_node(state: GraphState) -> dict: return _run_agent(DataQualityAgent, state)
def logic_node(state: GraphState) -> dict: return _run_agent(BusinessLogicAgent, state)
def anomaly_node(state: GraphState) -> dict: return _run_agent(AnomalyDetectorAgent, state)
def stale_node(state: GraphState) -> dict: return _run_agent(StaleRecordsAgent, state)

def parse_file_node(state: GraphState) -> dict:
    df_dict, metadata_dict = parse_file(state["file_bytes"], state["filename"])
    return {
        "dataframe": df_dict,
        "metadata": metadata_dict
    }

def aggregate_node(state: GraphState) -> dict:
    """Runs AFTER all parallel agents complete. Deduplicates and sorts issues."""
    issues = state.get("issues", [])
    
    # Deduplicate by (agent, title)
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.get("agent"), issue.get("title"))
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)
            
    # Sort by severity then confidence
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    unique_issues.sort(key=lambda x: (
        severity_order.get(x.get("severity", "LOW"), 3),
        -x.get("confidence", 0)
    ))
    
    return {"issues": unique_issues}

def synthesizer_node(state: GraphState) -> dict:
    agent = ReportSynthesizerAgent()
    start = time.time()
    result = agent.synthesize(state)
    duration = int((time.time() - start) * 1000)
    
    result["agent_statuses"] = [{
        "name": "report_synthesizer",
        "status": "done",
        "duration_ms": duration,
        "issue_count": 0
    }]
    result["generated_at"] = datetime.utcnow().isoformat()
    return result

def schema_node(state: GraphState) -> dict:
    start_time = time.time()
    agent = SchemaIntelligenceAgent()
    
    schema_updates = agent.get_schema_updates(state)
    
    duration = int((time.time() - start_time) * 1000)
    agent_status = {
        "name": "schema_intelligence",
        "status": "done",
        "duration_ms": duration,
        "issue_count": 0
    }
    
    schema_updates["agent_statuses"] = [agent_status]
    return schema_updates

def supervisor_node(state: GraphState) -> dict:
    start_time = time.time()
    agent = SupervisorAgent()
    
    agents_to_run = agent.decide_routing(state)
    
    duration = int((time.time() - start_time) * 1000)
    agent_status = {
        "name": "supervisor",
        "status": "done",
        "duration_ms": duration,
        "issue_count": 0
    }
    
    return {
        "agents_to_run": agents_to_run,
        "agent_statuses": [agent_status]
    }
