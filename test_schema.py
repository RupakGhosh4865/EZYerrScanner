import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from dotenv import load_dotenv
load_dotenv("backend/.env")

from backend.services.file_parser import parse_file
from backend.graph.nodes import schema_node, supervisor_node

def main():
    print("Parsing sample file...")
    try:
        with open("backend/sample_data/test_projects.csv", "rb") as f:
            file_bytes = f.read()
            
        df_dict, metadata_dict = parse_file(file_bytes, "test_projects.csv")
        
        state = {
            "file_bytes": file_bytes,
            "filename": "test_projects.csv",
            "dataframe": df_dict,
            "metadata": metadata_dict
        }
        
        print("\nRunning Schema Node...")
        schema_results = schema_node(state)
        print("=== SCHEMA RESULTS ===")
        print(json.dumps(schema_results, indent=2))
        
        state.update(schema_results)
        
        print("\nRunning Supervisor Node...")
        supervisor_results = supervisor_node(state)
        print("=== SUPERVISOR RESULTS ===")
        print(json.dumps(supervisor_results, indent=2))
    except Exception as e:
        print(f"Error testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
