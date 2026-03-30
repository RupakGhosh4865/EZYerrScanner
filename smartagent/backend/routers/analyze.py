"""
SmartAgent Analysis Router
POST /api/analyze/start  — runs the full LangGraph pipeline
GET  /api/analyze/connect — tests Smartsheet connectivity
"""
import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/analyze", tags=["analyze"])


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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
