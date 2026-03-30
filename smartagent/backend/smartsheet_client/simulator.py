import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

class SmartsheetSimulator:
    """
    Simulates the Smartsheet API using the pre-built JSON file.
    Identical interface to SmartsheetReader — swap by setting use_simulator=True.
    All write operations are logged but not actually executed.
    """
    
    SIMULATED_SHEET = {
        "id": "DEMO_SHEET_001",
        "name": "Q2 Project Tracker - Operations Team",
        "url": "https://app.smartsheet.com/sheets/demo",
        "columns": [
            {"id": 1001, "title": "Task ID", "type": "TEXT_NUMBER"},
            {"id": 1002, "title": "Task Name", "type": "TEXT_NUMBER"},
            {"id": 1003, "title": "Assigned To", "type": "CONTACT_LIST"},
            {"id": 1004, "title": "Status", "type": "PICKLIST",
             "options": ["Not Started","In Progress","Done","Blocked","Cancelled"]},
            {"id": 1005, "title": "Priority", "type": "PICKLIST",
             "options": ["High","Medium","Low"]},
            {"id": 1006, "title": "Start Date", "type": "DATE"},
            {"id": 1007, "title": "Due Date", "type": "DATE"},
            {"id": 1008, "title": "Budget ($)", "type": "TEXT_NUMBER"},
            {"id": 1009, "title": "Actual Cost ($)", "type": "TEXT_NUMBER"},
            {"id": 1010, "title": "Completion %", "type": "TEXT_NUMBER"},
            {"id": 1011, "title": "Department", "type": "PICKLIST",
             "options": ["Engineering","Marketing","Design","QA","Operations"]},
            {"id": 1012, "title": "Notes", "type": "TEXT_NUMBER"},
        ]
    }
    
    def list_sheets(self) -> List[Dict]:
        return [{"id": "DEMO_SHEET_001", 
                 "name": "Q2 Project Tracker - Operations Team",
                 "modified_at": "2025-01-15T10:30:00Z"}]
    
    def read_sheet(self, sheet_id: str) -> Tuple[pd.DataFrame, Dict, List[Dict], Dict]:
        """
        Build 45 rows of realistic project data with these embedded problems:
        - 3 exact duplicate rows (Task ID repeated)
        - 2 rows where Due Date is before Start Date  
        - 1 column (Notes) with 70% nulls
        - 5 overdue tasks still marked "In Progress"
        - Inconsistent Status: mix of "done", "Done", "DONE"
        - 2 rows with negative Budget values
        - 3 rows with Completion % > 100
        - 1 row with actual cost 4x the budget (anomaly)
        """
        rows = []
        base_date = datetime(2024, 1, 1)
        users = ["Alice Chen", "Bob Smith", "Charlie Davis", "Diana Prince", "Ethan Hunt"]
        depts = ["Engineering","Marketing","Design","QA","Operations"]
        statuses = ["Not Started","In Progress","Done","Blocked","Cancelled"]
        
        column_map = {col["title"]: col["id"] for col in self.SIMULATED_SHEET["columns"]}
        
        for i in range(1, 46):
            row_id = 10000 + i
            start_date = base_date + timedelta(days=i*2)
            due_date = start_date + timedelta(days=random.randint(5, 20))
            
            task_id = f"T-{1000+i}"
            status = random.choice(statuses)
            budget = random.randint(1000, 5000)
            actual = int(budget * random.uniform(0.5, 1.2))
            completion = 0 if status == "Not Started" else (100 if status == "Done" else random.randint(10, 90))
            
            # Inject Issues
            
            # 1. Exact Duplicates (Rows 10, 11, 12 repeat Row 9's ID)
            if i in [10, 11, 12]:
                task_id = "T-1009"
                
            # 2. Due Date before Start Date (Rows 15, 16)
            if i in [15, 16]:
                due_date = start_date - timedelta(days=2)
                
            # 3. Notes with 70% nulls (handled by not adding if random > 0.3)
            notes = f"Follow up on task {i}" if random.random() < 0.3 else None
            
            # 4. Overdue tasks in progress (Rows 20-24)
            if i in [20, 21, 22, 23, 24]:
                start_date = datetime.now() - timedelta(days=30)
                due_date = datetime.now() - timedelta(days=5)
                status = "In Progress"
            
            # 5. Inconsistent Status (Row 30)
            if i == 30:
                status = "done" # lowercase
            elif i == 31:
                status = "DONE" # uppercase
                
            # 6. Negative Budget (Rows 35, 36)
            if i in [35, 36]:
                budget = -500
                
            # 7. Completion % > 100 (Rows 40, 41, 42)
            if i in [40, 41, 42]:
                completion = 115
                
            # 8. Anomaly (Row 45 - cost 4x budget)
            if i == 45:
                budget = 1000
                actual = 4500
                
            row_dict = {
                "__row_id__": row_id,
                "__row_number__": i,
                "Task ID": task_id,
                "Task Name": f"Implementation Phase {i}",
                "Assigned To": random.choice(users),
                "Status": status,
                "Priority": random.choice(["High","Medium","Low"]),
                "Start Date": start_date.strftime("%Y-%m-%d"),
                "Due Date": due_date.strftime("%Y-%m-%d"),
                "Budget ($)": budget,
                "Actual Cost ($)": actual,
                "Completion %": completion,
                "Department": random.choice(depts),
                "Notes": notes
            }
            rows.append(row_dict)

        df = pd.DataFrame([ {k:v for k,v in r.items() if not k.startswith("__")} for r in rows ])
        
        metadata = {
            "sheet_id": "DEMO_SHEET_001",
            "sheet_name": "Q2 Project Tracker - Operations Team",
            "rows": 45,
            "columns": 12,
            "url": "https://app.smartsheet.com/sheets/demo"
        }
        
        return df, metadata, rows, column_map
    
    def simulate_write(self, action: Dict) -> Dict:
        """Logs what would have been written. Returns simulated success response."""
        print(f"[SIMULATOR] Action: {action['action_type']} on Row {action['target_row_id']}")
        return {
            "status": "simulated_success",
            "message": f"[DEMO] Would have executed: {action['action_type']} on row {action['target_row_id']}",
            "action": action
        }
