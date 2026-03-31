"""
SmartAgent Analysis Router
POST /api/analyze/start  — runs the full LangGraph pipeline
GET  /api/analyze/connect — tests Smartsheet connectivity
"""
import os
import asyncio
import uuid
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Any

# EZYerr Scanner Imports (Original)
from models_ezyerr.schemas import AnalysisReport
from graph_ezyerr.graph_builder import ezyerr_graph
from graph_ezyerr.nodes import parse_file_node, schema_node, supervisor_node

router = APIRouter(prefix="/analyze", tags=["analyze"])
FILE_STORE: Dict[str, bytes] = {} # Simple in-memory storage for HITL session bytes


class AnalyzeRequest(BaseModel):
    sheet_id: str


@router.post("/plan")
async def get_analysis_plan(file: UploadFile = File(...)):
    """
    Original File Scanner: Phase 1 — Generate Analysis Plan
    """
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


@router.post("/execute", response_model=AnalysisReport)
async def execute_analysis_plan(state: dict):
    """
    Original File Scanner: Phase 2 — Execute Analysis Plan
    """
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


class AnalyzeRequest(BaseModel):
    sheet_id: str


@router.get("/connect")
async def test_connection():
    """
    Tests connection to Smartsheet (WireMock or real).
    Returns list of accessible sheets.
    """
    from smartsheet_client.reader import SmartsheetReader
    reader = SmartsheetReader()
    try:
        sheets = reader.list_sheets()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Smartsheet connection failed: {str(e)}")

    mode = "mock_wiremock" if os.getenv("USE_MOCK_SERVER", "true").lower() == "true" else "live_smartsheet"
    return {
        "mode": mode,
        "sheets": sheets,
        "wiremock_url": os.getenv("SMARTSHEET_MOCK_URL", "http://localhost:8082")
    }


@router.post("/start")
async def start_analysis(request: AnalyzeRequest):
    """
    Runs the full LangGraph pipeline:
      load → schema → supervisor → agents → aggregator → synthesizer
    Returns the complete analysis state including proposed_actions for HITL review.
    """
    from graph.graph_builder import smartagent_graph

    initial_state = {
        "sheet_id": request.sheet_id,
        "sheet_name": "",
        "use_mock_server": os.getenv("USE_MOCK_SERVER", "true").lower() == "true",
        "mock_test_name_prefix": "smartagent-",
        "smartsheet_token": os.getenv("SMARTSHEET_ACCESS_TOKEN", ""),
        "dataframe": [],
        "metadata": {},
        "raw_rows": [],
        "column_map": {},
        "domain": "",
        "column_types": {},
        "primary_key_cols": [],
        "date_col_pairs": [],
        "agents_to_run": [],
        "issues": [],
        "agent_statuses": [],
        "proposed_actions": [],
        "approved_action_ids": [],
        "executed_actions": [],
        "audit_sheet_url": "",
        "health_score": 100,
        "executive_summary": "",
        "top_priorities": [],
        "generated_at": "",
    }

    try:
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None, smartagent_graph.invoke, initial_state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return {
        "sheet_id": request.sheet_id,
        "sheet_name": final_state.get("sheet_name", ""),
        "health_score": final_state.get("health_score", 0),
        "domain": final_state.get("domain", ""),
        "issues": final_state.get("issues", []),
        "proposed_actions": final_state.get("proposed_actions", []),
        "agent_statuses": final_state.get("agent_statuses", []),
        "executive_summary": final_state.get("executive_summary", ""),
        "top_priorities": final_state.get("top_priorities", []),
        "column_map": final_state.get("column_map", {}),
        "generated_at": final_state.get("generated_at", ""),
    }
