"""
SmartAgent Actions Router
POST /api/actions/execute — executes approved actions against Smartsheet
"""
import io
import csv
import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/actions", tags=["actions"])
logger = logging.getLogger("uvicorn.error")


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
        logger.error(f"Action execution error: {str(e)}")
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
        # Load the latest state of the sheet
        records, _meta, raw_rows, _column_map = reader.read_sheet(request.sheet_id)
    except Exception as e:
        logger.error(f"CSV Export Error: Failed to load sheet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load sheet for CSV export: {str(e)}")

    # Map row_id -> record index (support both int and string IDs)
    row_id_to_idx = {}
    for idx, rr in enumerate(raw_rows):
        rid = rr.get("__row_id__")
        if rid is not None:
            row_id_to_idx[str(rid)] = idx
            try:
                row_id_to_idx[int(rid)] = idx
            except: pass

    approved = set(request.approved_action_ids or [])
    proposed = request.proposed_actions or []

    # Apply approved updates to the records in memory
    logger.info(f"Applying {len(approved)} approved actions to {len(records)} records...")
    for action in proposed:
        aid = action.get("action_id")
        if aid not in approved:
            continue
            
        atype = action.get("action_type")
        if atype not in ("update_cell_value", "update_status"):
            logger.warning(f"Skipping action {aid} of type {atype}")
            continue

        target_row_id = action.get("target_row_id")
        column_title = action.get("column_title") or "Status"
        proposed_value = action.get("proposed_value")
        
        if target_row_id is None:
            logger.warning(f"Action {aid} missing target_row_id")
            continue
            
        # Try finding row by original type, then by string
        rec_idx = row_id_to_idx.get(target_row_id)
        if rec_idx is None:
            rec_idx = row_id_to_idx.get(str(target_row_id))
            
        if rec_idx is not None and rec_idx < len(records):
            # Find the actual key in record (case-insensitive check to match CSV headers)
            target_key = str(column_title)
            actual_key = next((k for k in records[rec_idx].keys() if k.lower() == target_key.lower()), target_key)
            old_val = records[rec_idx].get(actual_key)
            records[rec_idx][actual_key] = "" if proposed_value is None else str(proposed_value)
            logger.info(f"Fixed Row {target_row_id} [{actual_key}]: '{old_val}' -> '{records[rec_idx][actual_key]}'")
        else:
            logger.error(f"Failed to find Row {target_row_id} in {len(records)} records")

    # Determine CSV headers
    if request.column_map and len(request.column_map) > 0:
        fieldnames = list(request.column_map.keys())
    else:
        keys = []
        if records:
            keys = list(records[0].keys())
        fieldnames = keys if keys else ["Sheet Data"]

    try:
        # Generate CSV bytes in memory
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            # Cast all values to string to avoid serialization errors
            writer.writerow({k: "" if r.get(k) is None else str(r.get(k)) for k in fieldnames})

        # Sanitize filename: remove non-ASCII characters (like em-dash) which break HTTP headers
        base_name = (request.sheet_name or 'sheet').replace(' ', '_')
        safe_name = base_name.encode('ascii', 'ignore').decode('ascii')
        filename = f"{safe_name}_corrected.csv"
        
        data = buf.getvalue().encode("utf-8")
        return StreamingResponse(
            io.BytesIO(data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"CSV Export Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV formatting error: {str(e)}")
