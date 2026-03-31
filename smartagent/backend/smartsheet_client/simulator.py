import os
import csv
from datetime import datetime
from typing import List, Dict, Tuple, Any

class SmartsheetSimulator:
    """
    Simulates the Smartsheet API using the q2_tracker.csv dataset.
    Identical interface to SmartsheetReader — swap by setting use_simulator=True.
    All write operations are logged but not actually executed.
    """
    
    def __init__(self):
        # Locate the CSV dataset from the script directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.abspath(os.path.join(current_dir, "..", "all_agents_dataset.csv"))
        # Allow swapping datasets without code changes
        # Example: SIMULATOR_CSV_PATH=.../scripts/all_agents_dataset.csv
        self.csv_path = os.path.abspath(os.getenv("SIMULATOR_CSV_PATH", default_path))
        
        self.SIMULATED_SHEET = {
            "id": "STRESS_TEST_001",
            "name": "Q2 Project Tracker (Stress Test)",
            "url": "https://app.smartsheet.com/sheets/stress-test",
            "columns": []
        }
    
    def list_sheets(self) -> List[Dict]:
        dataset_name = os.path.basename(self.csv_path)
        return [{
            "id": "STRESS_TEST_001",
            "name": f"Simulator Dataset — {dataset_name}",
            "modified_at": datetime.now().isoformat()
        }]
    
    def read_sheet(self, sheet_id: str) -> Tuple[list[dict], Dict, List[Dict], Dict]:
        """
        Loads data from a CSV file and formats it for the SmartAgent analysis pipeline.
        Returns:
          (records, metadata, rows_json, column_map)
        """
        if not os.path.exists(self.csv_path):
            # Fallback to a minimal set if the file is missing — but we expect it to be there.
            raise FileNotFoundError(
                f"Simulator dataset missing at {self.csv_path}. "
                f"Generate one with scripts/multi_agent_test_dataset.py or set SIMULATOR_CSV_PATH."
            )

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = [dict(r) for r in reader]
            columns = list(reader.fieldnames or [])
        
        # 1. Update columns dynamically from CSV headers
        self.SIMULATED_SHEET["columns"] = []
        column_map = {}
        for i, col_title in enumerate(columns):
            col_id = 1000 + i
            self.SIMULATED_SHEET["columns"].append({
                "id": col_id,
                "title": col_title,
                "type": "CURRENCY" if "cost" in col_title.lower() or "budget" in col_title.lower() else "TEXT_NUMBER"
            })
            column_map[col_title] = col_id
        
        # 2. Build rows in Smartsheet JSON format
        rows_json = []
        for i, row in enumerate(records):
            row_id = 20000 + i
            row_dict = {
                "__row_id__": row_id,
                "__row_number__": i + 1
            }
            # Add all columns from CSV
            for col_title in columns:
                val = row.get(col_title, "")
                if val in ("", "—", "N/A", "None", "null"):
                    val = None
                row_dict[col_title] = val
                
            rows_json.append(row_dict)

        metadata = {
            "sheet_id": "STRESS_TEST_001",
            "sheet_name": f"Simulator Dataset — {os.path.basename(self.csv_path)}",
            "rows": len(records),
            "columns": len(columns),
            "url": "https://app.smartsheet.com/sheets/stress-test"
        }
        
        print(f"[SIMULATOR] Loaded {len(records)} rows from {self.csv_path}")
        return records, metadata, rows_json, column_map
    
    def simulate_write(self, action: Dict) -> Dict:
        """Logs what would have been written. Returns simulated success response."""
        print(f"[SIMULATOR] Action: {action['action_type']} on Row {action['target_row_id']}")
        return {
            "status": "simulated_success",
            "message": f"[SIMULATOR] Would have executed: {action['action_type']} on row {action['target_row_id']}",
            "action": action
        }
