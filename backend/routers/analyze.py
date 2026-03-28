import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException
from ..models.schemas import AnalysisReport
from ..graph.graph_builder import optiscan_graph
from ..graph.state import GraphState

router = APIRouter()

@router.post("/analyze", response_model=AnalysisReport)
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls', '.json')):
        raise HTTPException(422, "Unsupported file type. Use CSV, XLSX, or JSON.")
    
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large. Maximum 10MB.")
    
    initial_state: GraphState = {
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
    
    try:
        final_state = await asyncio.get_event_loop().run_in_executor(
            None, optiscan_graph.invoke, initial_state
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
