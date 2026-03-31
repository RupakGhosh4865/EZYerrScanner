from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import os
from config import get_smartsheet_client
from smartsheet_client.simulator import SmartsheetSimulator

router = APIRouter(prefix="/connect", tags=["connection"])

@router.get("/test")
async def test_connection():
    """
    Test connection to Smartsheet (or Simulator).
    """
    use_simulator = os.getenv("USE_SIMULATOR", "true").lower() == "true"
    
    if use_simulator:
        sim = SmartsheetSimulator()
        return {
            "mode": "simulator",
            "sheets": sim.list_sheets(),
            "user_name": "Demo User"
        }
    
    try:
        client = get_smartsheet_client(test_name="list-sheets")
        # In real SDK, client is smartsheet.Smartsheet object
        # In mock client, it has same interface
        response = client.Sheets.list_sheets()

        # Some SDK versions return an Error object instead of a response with .data
        if not hasattr(response, "data"):
            error_msg = getattr(response, "message", str(response))
            raise RuntimeError(f"Smartsheet SDK returned error instead of sheet list: {error_msg}")
        
        sheets = [
            {
                "id": str(s.id),
                "name": s.name,
                "modified_at": str(getattr(s, "modified_at", "")),
            }
            for s in response.data
        ]
        
        return {
            "mode": "real",
            "sheets": sheets,
            "user_name": "Authenticated User"
        }
    except Exception as e:
        # Detailed logging for debugging SDK errors
        try:
            client = get_smartsheet_client(test_name="debug")
            print(f"DEBUG: Smartsheet API Exception: {type(e).__name__} - {type(e).__name__}: {str(e)}")
            
            # If it returned an Error-like object but didn't raise
            response = client.Sheets.list_sheets()
            if hasattr(response, "result") and hasattr(getattr(response, "result", None), "error_code"):
                print(f"DEBUG: SDK Error Object: {response.result}")
            elif hasattr(response, "message"):
                print(f"DEBUG: SDK Error Message: {response.message}")
        except Exception as inner:
            print(f"DEBUG: Secondary debug call failed: {type(inner).__name__}: {str(inner)}")

        raise HTTPException(status_code=401, detail=f"Smartsheet connection failed: {str(e)}")

@router.get("/sheet/{sheet_id}")
async def get_sheet_metadata(sheet_id: str):
    """
    Fetch specific sheet metadata to validate access.
    """
    use_simulator = os.getenv("USE_SIMULATOR", "true").lower() == "true"
    
    if use_simulator:
        sim = SmartsheetSimulator()
        df, meta, rows, col_map = sim.read_sheet(sheet_id)
        return meta

    try:
        client = get_smartsheet_client(test_name="get-sheet")
        sheet = client.Sheets.get_sheet(sheet_id)
        return {
            "id": str(sheet.id),
            "name": sheet.name,
            "row_count": sheet.total_row_count,
            "columns": [c.title for c in sheet.columns],
            "url": sheet.permalink
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Sheet {sheet_id} not found or access denied: {str(e)}")
