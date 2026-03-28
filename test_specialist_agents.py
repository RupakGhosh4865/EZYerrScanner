import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv("backend/.env")

from backend.services.file_parser import parse_file
from backend.graph.nodes import (
    duplicate_node, quality_node, logic_node, 
    anomaly_node, stale_node
)

def test_agents():
    print("Parsing sample file...")
    try:
        with open("backend/sample_data/test_projects.csv", "rb") as f:
            file_bytes = f.read()
            
        df_dict, metadata_dict = parse_file(file_bytes, "test_projects.csv")
        
        state = {
            "file_bytes": file_bytes,
            "filename": "test_projects.csv",
            "dataframe": df_dict,
            "metadata": metadata_dict,
            "domain": "project_management",
            "column_types": {
                "task_id": "id",
                "task_name": "name",
                "assignee": "name",
                "status": "status",
                "priority": "text",
                "start_date": "date",
                "due_date": "date",
                "end_date": "date",
                "budget": "numeric",
                "actual_cost": "numeric",
                "client_feedback": "text",
                "updated_at": "date",
                "project_code": "id",
                "department": "text",
                "completion_pct": "percentage"
            },
            "primary_key_cols": ["task_id"],
            "date_col_pairs": [["start_date", "due_date"], ["start_date", "end_date"]],
            "agents_to_run": [
                "duplicate_hunter", "data_quality", "business_logic", 
                "anomaly_detector", "stale_records"
            ]
        }

        nodes = [
            ("Duplicate Hunter", duplicate_node),
            ("Data Quality", quality_node),
            ("Business Logic", logic_node),
            ("Anomaly Detector", anomaly_node),
            ("Stale Records", stale_node)
        ]

        for name, node_func in nodes:
            print(f"\n--- Testing {name} ---")
            res = node_func(state)
            status = res.get("agent_statuses", [{}])[0]
            print(f"Status: {status.get('status')} | Time: {status.get('duration_ms')}ms | Issues Found: {status.get('issue_count')}")
            
            issues = res.get("issues", [])
            for i, issue in enumerate(issues[:2]): # Print first 2 issues to not clutter
               print(f"[{i+1}] {issue.get('title', 'Unknown')} (Severity: {issue.get('severity', 'Unknown')})")
               print(f"    {issue.get('description', '')[:100]}...")
            
            if len(issues) > 2:
                print(f"    ... and {len(issues)-2} more issues.")

    except Exception as e:
        print(f"Error testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agents()
