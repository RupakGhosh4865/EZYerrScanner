import sys
import os

# Move to backend to allow imports
backend_path = r'd:\EZYerrScanner\smartagent\backend'
os.chdir(backend_path)
sys.path.append(backend_path)

from smartsheet_client.simulator import SmartsheetSimulator

try:
    print("Testing SmartsheetSimulator sync...")
    sim = SmartsheetSimulator()
    df, metadata, rows, col_map = sim.read_sheet("STRESS_TEST_001")
    
    print(f"✅ Loaded rows: {len(df)}")
    print(f"✅ Metadata rows: {metadata.get('rows')}")
    print(f"✅ First task: {df.iloc[0]['task_id']}")
    print(f"✅ Number of columns: {len(df.columns)}")
    
    if len(df) == 162:
        print("🎉 SUCCESS: Simulator is now synchronized with 162-row dataset.")
    else:
        print(f"❌ FAILURE: Expected 162 rows, but got {len(df)}.")

except Exception as e:
    print(f"❌ ERROR: {e}")
