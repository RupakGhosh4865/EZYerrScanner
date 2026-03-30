import pandas as pd
import sys
import os

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
        client = self._client_factory(test_name="list-sheets")
        response = client.Sheets.list_sheets()
        
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
        Loads a full sheet and converts it into a pandas DataFrame.
        Scenario: "get-sheet"
        
        Returns:
          (df, metadata, raw_rows, column_map)
        """
        client = self._client_factory(test_name="get-sheet")
        sheet = client.Sheets.get_sheet(int(sheet_id))
        
        # 1. Map column IDs to titles
        column_map = {col.title: col.id for col in sheet.columns}
        col_id_to_title = {col.id: col.title for col in sheet.columns}
        
        # 2. Build rows as list of dicts
        raw_rows = []
        for row in sheet.rows:
            row_dict = {
                "__row_id__": row.id,
                "__row_number__": row.row_number
            }
            # Add cell values
            for cell in row.cells:
                col_title = col_id_to_title.get(cell.column_id, f"Unknown_{cell.column_id}")
                # Prefer displayValue for formatted text
                row_dict[col_title] = cell.display_value if cell.display_value is not None else cell.value
                
            raw_rows.append(row_dict)
            
        # 3. Create DataFrame
        if not raw_rows:
            df = pd.DataFrame(columns=list(column_map.keys()))
        else:
            df = pd.DataFrame(raw_rows)
            # Drop the internal row identifiers for the analysis-ready DF
            df = df.drop(columns=["__row_id__", "__row_number__"], errors='ignore')
            
        # 4. Metadata
        metadata = {
            "sheet_id": str(sheet.id),
            "sheet_name": sheet.name,
            "permalink": getattr(sheet, "permalink", ""),
            "row_count": sheet.total_row_count,
            "columns": [col.title for col in sheet.columns]
        }
        
        return df, metadata, raw_rows, column_map

    def get_column_id(self, sheet_id: str, column_title: str) -> int | None:
        """Helper to get a column ID by title."""
        _, _, _, column_map = self.read_sheet(sheet_id)
        return column_map.get(column_title)
