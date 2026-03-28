import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(".env")

from backend.graph.graph_builder import optiscan_graph

def test_with_sample():
    with open("sample_data/test_projects.csv", "rb") as f:
        file_bytes = f.read()
    
    initial_state = {
        "file_bytes": file_bytes,
        "filename": "test_projects.csv",
        "dataframe": {},
        "metadata": {},
        "domain": "generic",
        "column_types": {},
        "primary_key_cols": [],
        "date_col_pairs": [],
        "agents_to_run": [],
        "issues": [],
        "agent_statuses": [],
        "health_score": 100,
        "executive_summary": "",
        "top_priorities": [],
        "generated_at": ""
    }
    
    print("Invoking full pipeline. This might take 30-60 seconds...")
    try:
        result = optiscan_graph.invoke(initial_state)
        
        print("\n" + "="*50)
        print(f"Domain detected: {result.get('domain')}")
        print(f"Agents ran: {result.get('agents_to_run')}")
        print(f"Issues found: {len(result.get('issues', []))}")
        print(f"Health score: {result.get('health_score')}")
        print(f"\nExecutive Summary:\n{result.get('executive_summary')}")
        print(f"\nTop Priorities:")
        for p in result.get('top_priorities', []):
            print(f"  - {p}")
        print(f"\nAll Issues:")
        for issue in result.get('issues', []):
            print(f"  [{issue.get('severity', 'Unknown')}] {issue.get('title', 'Unknown')} (agent: {issue.get('agent', 'Unknown')})")
        print("="*50)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_sample()
