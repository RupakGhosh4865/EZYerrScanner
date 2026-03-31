"""
SmartAgent Actions Router
POST /api/actions/execute — executes approved actions against Smartsheet
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import io
import csv

router = APIRouter(prefix="/actions", tags=["actions"])


class ExecuteRequest(BaseModel):
    sheet_id: str
    approved_action_ids: List[str]
    proposed_actions: List[Dict[str, Any]]
    column_map: Dict[str, Any]
    issues: List[Dict[str, Any]]
    health_score: int
    sheet_name: str


class DownloadCsvRequest(BaseModel):
    sheet_id: str
    approved_action_ids: List[str]
    proposed_actions: List[Dict[str, Any]]
    column_map: Dict[str, Any]
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


@router.post("/download_csv")
async def download_corrected_csv(request: DownloadCsvRequest):
    """
    Builds a "corrected" CSV by applying approved actions to the latest sheet snapshot.
    In mock mode, write actions are simulated, but CSV export still reflects approved cell updates.
    """
    from smartsheet_client.reader import SmartsheetReader

    reader = SmartsheetReader()
    try:
        records, _meta, raw_rows, _column_map = reader.read_sheet(request.sheet_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sheet for CSV export: {str(e)}")

    # Map row_id -> record index
    row_id_to_idx: dict[int, int] = {}
    for idx, rr in enumerate(raw_rows):
        rid = rr.get("__row_id__")
        if rid is None:
            continue
        try:
            row_id_to_idx[int(rid)] = idx
        except Exception:
            continue

    approved = set(request.approved_action_ids or [])
    proposed = request.proposed_actions or []

    for action in proposed:
        if action.get("action_id") not in approved:
            continue
        atype = action.get("action_type")
        if atype not in ("update_cell_value", "update_status"):
            continue

        target_row_id = action.get("target_row_id")
        column_title = action.get("column_title") or "Status"
        proposed_value = action.get("proposed_value")
        if target_row_id is None:
            continue
        rec_idx = row_id_to_idx.get(int(target_row_id), None)
        if rec_idx is None or rec_idx >= len(records):
            continue
        records[rec_idx][str(column_title)] = "" if proposed_value is None else str(proposed_value)

    # Column order: prefer column_map keys; else union of record keys
    if request.column_map:
        fieldnames = list(request.column_map.keys())
    else:
        keys = set()
        for r in records:
            keys.update(r.keys())
        fieldnames = sorted(keys)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        writer.writerow({k: r.get(k, "") for k in fieldnames})

    filename = f"{(request.sheet_name or 'sheet').replace(' ', '_')}_corrected.csv"
    data = buf.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
