import sys
import os
# No pytest needed for basic run

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from smartsheet_client.reader import SmartsheetReader
from smartsheet_client.writer import SmartsheetWriter

class TestSmartsheetReader:
    
    def test_list_sheets_returns_data(self):
        reader = SmartsheetReader()
        sheets = reader.list_sheets()
        print(f"\n--- list_sheets: {len(sheets)} found ---")
        assert len(sheets) > 0
        assert "id" in sheets[0]
        assert "name" in sheets[0]
        print(f"  Sheets: {[s['name'] for s in sheets]}")
    
    def test_read_sheet_returns_dataframe(self):
        reader = SmartsheetReader()
        sheets = reader.list_sheets()
        sheet_id = sheets[0]["id"]
        
        records, meta, raw_rows, col_map = reader.read_sheet(sheet_id)
        
        print("\n--- read_sheet test ---")
        assert records is not None
        assert len(records) > 0
        assert len(col_map) > 0
        assert all("__row_id__" in r for r in raw_rows)
        assert meta["sheet_name"] is not None
        print(f"  Records: {len(records)} rows")
        print(f"  Columns: {list(records[0].keys())}")
        print(f"  Column map: {col_map}")
    
    def test_raw_rows_have_row_ids(self):
        reader = SmartsheetReader()
        sheets = reader.list_sheets()
        _, _, raw_rows, _ = reader.read_sheet(sheets[0]["id"])
        
        for row in raw_rows:
            assert "__row_id__" in row
            assert isinstance(row["__row_id__"], int)

class TestSmartsheetWriter:
    
    def setup_method(self):
        reader = SmartsheetReader()
        sheets = reader.list_sheets()
        sheet_id = sheets[0]["id"]
        _, _, self.raw_rows, self.col_map = reader.read_sheet(sheet_id)
        self.sheet_id = sheet_id
        self.writer = SmartsheetWriter(sheet_id, self.col_map)
    
    def test_add_comment_to_row(self):
        row_id = self.raw_rows[0]["__row_id__"]
        print(f"\n--- add_comment to row {row_id} ---")
        result = self.writer.add_row_comment(
            row_id=row_id,
            comment_text="[AI AUDIT] Test comment from SmartAgent"
        )
        assert result["status"] == "success"
        print(f"  Result: {result}")
    
    def test_flag_cell(self):
        row_id = self.raw_rows[0]["__row_id__"]
        first_col = list(self.col_map.keys())[0]
        print(f"\n--- flag_cell to row {row_id} col {first_col} ---")
        result = self.writer.flag_cell(
            row_id=row_id,
            column_title=first_col,
            note="Data quality issue detected"
        )
        assert result["status"] == "success"
    
    def test_update_cell_value(self):
        row_id = self.raw_rows[0]["__row_id__"]
        status_col = next((k for k in self.col_map if "status" in k.lower()), 
                          list(self.col_map.keys())[0])
        print(f"\n--- update_cell_value to row {row_id} col {status_col} ---")
        result = self.writer.update_cell_value(
            row_id=row_id,
            column_title=status_col,
            new_value="Needs Review"
        )
        assert result["status"] == "success"
    
    def test_create_audit_sheet(self):
        fake_issues = [
            {"id": "1", "severity": "HIGH"}
        ]
        print(f"\n--- create_audit_sheet ---")
        result = self.writer.create_audit_sheet(
            issues=fake_issues,
            health_score=72,
            source_sheet_name="Q2 Project Tracker"
        )
        assert result["status"] == "success"
        assert "sheet_id" in result
        print(f"  Audit sheet created: {result.get('sheet_name')} (ID: {result.get('sheet_id')})")

if __name__ == "__main__":
    # Manual run
    t = TestSmartsheetReader()
    t.test_list_sheets_returns_data()
    t.test_read_sheet_returns_dataframe()
    t.test_raw_rows_have_row_ids()
    
    tw = TestSmartsheetWriter()
    tw.setup_method()
    tw.test_add_comment_to_row()
    tw.test_flag_cell()
    tw.test_update_cell_value()
    tw.test_create_audit_sheet()
    print("\n[SUCCESS] All SmartAgent Phase 2 tests passed against WireMock.")
