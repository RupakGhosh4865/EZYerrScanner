import asyncio
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from models.schemas import AnalysisReport
from graph.graph_builder import ezyerr_graph
from graph.state import GraphState

from graph.nodes import parse_file_node, schema_node, supervisor_node, duplicate_node, quality_node, logic_node, anomaly_node, stale_node, aggregate_node, synthesizer_node

router = APIRouter()
FILE_STORE = {} # Simple in-memory storage for HITL session bytes

@router.post("/analyze/plan")
async def get_analysis_plan(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls', '.json')):
        raise HTTPException(422, "Unsupported file type. Use CSV, XLSX, or JSON.")
    
    file_bytes = await file.read()
    session_id = str(uuid.uuid4())
    FILE_STORE[session_id] = file_bytes

    initial_state = {
        "file_bytes": file_bytes,
        "filename": file.filename,
        "dataframe": {},
        "metadata": {},
        "domain": "generic",
        "column_types": {},
        "primary_key_cols": [],
        "date_col_pairs": [],
        "agents_to_run": [],
        "issues": [],
        "agent_statuses": [],
        "health_score": 100,
        "executive_summary": "",
        "top_priorities": [],
        "generated_at": ""
    }
    
    # Run nodes sequentially for the plan phase
    state = initial_state
    
    # Node 1: Parse File
    parse_results = parse_file_node(state)
    state.update(parse_results)
    
    # Node 2: Schema Intelligence
    schema_results = schema_node(state)
    state.update(schema_results)
    
    # Node 3: Supervisor Decisions
    supervisor_results = supervisor_node(state)
    state.update(supervisor_results)
    
    # Cleanup for response
    state.pop("file_bytes", None)
    state.pop("dataframe", None) 
    state["session_id"] = session_id
    
    return state

@router.post("/analyze/execute", response_model=AnalysisReport)
async def execute_analysis_plan(state: dict):
    session_id = state.get("session_id")
    if not session_id or session_id not in FILE_STORE:
        raise HTTPException(400, "Invalid or expired session. Please re-upload.")
    
    # Restore bytes for the graph execution
    state["file_bytes"] = FILE_STORE.pop(session_id)
    
    try:
        final_state = await asyncio.get_event_loop().run_in_executor(
            None, ezyerr_graph.invoke, state
        )
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    
    issues_by_severity = {
        "HIGH": sum(1 for i in final_state.get("issues", []) if i.get("severity") == "HIGH"),
        "MEDIUM": sum(1 for i in final_state.get("issues", []) if i.get("severity") == "MEDIUM"),
        "LOW": sum(1 for i in final_state.get("issues", []) if i.get("severity") == "LOW"),
    }
    
    return AnalysisReport(
        metadata=final_state.get("metadata", {}),
        domain=final_state.get("domain", "generic"),
        health_score=final_state.get("health_score", 100),
        issues=final_state.get("issues", []),
        agent_statuses=final_state.get("agent_statuses", []),
        executive_summary=final_state.get("executive_summary", ""),
        top_priorities=final_state.get("top_priorities", []),
        generated_at=final_state.get("generated_at", ""),
        total_issues_by_severity=issues_by_severity
    )
