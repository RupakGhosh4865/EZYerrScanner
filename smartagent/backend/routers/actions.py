"""
SmartAgent Actions Router
POST /api/actions/execute — executes approved actions against Smartsheet
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/actions", tags=["actions"])


class ExecuteRequest(BaseModel):
    sheet_id: str
    approved_action_ids: List[str]
    proposed_actions: List[Dict[str, Any]]
    column_map: Dict[str, Any]
    issues: List[Dict[str, Any]]
    health_score: int
    sheet_name: str


@router.post("/execute")
async def execute_actions(request: ExecuteRequest):
    """
    Called after the human approves actions in the UI.
    Runs execute_actions_node with the approved action IDs against WireMock/Smartsheet.
    Returns list of executed actions + audit sheet URL.
    """
    from graph.nodes import execute_actions_node

    state = {
        "sheet_id": request.sheet_id,
        "approved_action_ids": request.approved_action_ids,
        "proposed_actions": request.proposed_actions,
        "column_map": request.column_map,
        "issues": request.issues,
        "health_score": request.health_score,
        "sheet_name": request.sheet_name,
    }

    try:
        result = execute_actions_node(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")

    executed = result.get("executed_actions", [])
    return {
        "executed_actions": executed,
        "audit_sheet_url": result.get("audit_sheet_url", ""),
        "total_executed": len(executed),
        "success_count": sum(1 for a in executed if a.get("status") in ("success", "simulated_success")),
        "failed_count": sum(1 for a in executed if a.get("status") == "failed"),
    }
