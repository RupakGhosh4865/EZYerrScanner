import sys
import os
import json

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_smartsheet_client

class SmartsheetReader:
    """
    Reads data from Smartsheet using the official SDK.
    Supports both real Smartsheet API and WireMock server.
    """

    def __init__(self):
        self._client_factory = get_smartsheet_client

    def list_sheets(self) -> list[dict]:
        """
        Retrieves a list of available sheets.
        Scenario: "list-sheets"
        """
        use_simulator = os.getenv("USE_SIMULATOR", "false").lower() == "true"
        if use_simulator:
            from smartsheet_client.simulator import SmartsheetSimulator
            sim = SmartsheetSimulator()
            return sim.list_sheets()

        client = self._client_factory(test_name="list-sheets")
        response = client.Sheets.list_sheets()

        # Some SDK paths may return an Error object without .data
        if not hasattr(response, "data"):
            error_msg = getattr(response, "message", str(response))
            raise RuntimeError(f"Smartsheet SDK returned error instead of sheet list: {error_msg}")
        
        sheets = []
        for sheet in response.data:
            sheets.append({
                "id": str(sheet.id),
                "name": sheet.name,
                "modified_at": str(getattr(sheet, "modified_at", "")),
                # totalRowCount is often in the sheet summary or list response
                "row_count": getattr(sheet, "total_row_count", 0),
            })
        return sheets

    def read_sheet(self, sheet_id: str) -> tuple:
        """
        Loads a full sheet and returns row records (list[dict]).
        Scenario: "get-sheet"
        
        Returns:
          (records, metadata, raw_rows, column_map)
        """
        use_simulator = os.getenv("USE_SIMULATOR", "false").lower() == "true"
        if use_simulator:
            from smartsheet_client.simulator import SmartsheetSimulator
            sim = SmartsheetSimulator()
            records, metadata, rows_json, column_map = sim.read_sheet(sheet_id)
            # Simulator already returns analysis-ready records and raw_rows-like json
            return records, metadata, rows_json, column_map

        client = self._client_factory(test_name="get-sheet")
        sheet = client.Sheets.get_sheet(int(sheet_id))
        
        # 1. Map column IDs to titles
        column_map = {col.title: col.id for col in sheet.columns}
        col_id_to_title = {col.id: col.title for col in sheet.columns}
        
        # 2. Build rows as list of dicts
        raw_rows = []
        records = []
        for row in sheet.rows:
            # Some mock/live responses may omit row.id; fall back to cell.row_id if available.
            row_id = getattr(row, "id", None)
            if row_id is None:
                try:
                    first_cell = row.cells[0] if getattr(row, "cells", None) else None
                    row_id = getattr(first_cell, "row_id", None)
                except Exception:
                    row_id = None

            row_dict = {
                "__row_id__": row_id,
                "__row_number__": row.row_number
            }
            rec = {}
            # Add cell values
            for cell in row.cells:
                col_title = col_id_to_title.get(cell.column_id, f"Unknown_{cell.column_id}")
                col_title = str(col_title)
                # Prefer displayValue for formatted text
                val = cell.display_value if cell.display_value is not None else cell.value
                # Ensure values are JSON/pandas friendly (avoid numpy arrays / complex objects)
                if hasattr(val, "tolist"):  # e.g. numpy arrays
                    try:
                        val = val.tolist()
                    except Exception:
                        val = str(val)
                if isinstance(val, (dict, list, tuple, set)):
                    try:
                        val = json.dumps(val, default=str)
                    except Exception:
                        val = str(val)
                row_dict[col_title] = val
                rec[col_title] = val
                
            raw_rows.append(row_dict)
            records.append(rec)
            
        # 4. Metadata
        metadata = {
            "sheet_id": str(sheet.id),
            "sheet_name": sheet.name,
            "permalink": getattr(sheet, "permalink", ""),
            "row_count": sheet.total_row_count,
            "columns": [col.title for col in sheet.columns]
        }
        
        return records, metadata, raw_rows, column_map

    def get_column_id(self, sheet_id: str, column_title: str) -> int | None:
        """Helper to get a column ID by title."""
        _, _, _, column_map = self.read_sheet(sheet_id)
        return column_map.get(column_title)
