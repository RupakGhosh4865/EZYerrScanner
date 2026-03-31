import requests
import json
import time
import os
import sys

# Ensure UTF-8 printing on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BACKEND_URL = "http://localhost:8000/api/analyze/start"
SHEET_ID = "4583173393803140"

def run_stress_test():
    print(f"🚀 Initializing SmartAgent Stress Test for Sheet {SHEET_ID}...")
    print(f"Connecting to backend at {BACKEND_URL}...")
    
    payload = {"sheet_id": SHEET_ID}
    start_time = time.time()
    
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Analysis failed (HTTP {response.status_code})")
            print(response.text)
            return

        data = response.json()
        duration = time.time() - start_time
        
        print(f"\n✅ Analysis Completed in {duration:.2f}s")
        print(f"{'━'*60}")
        print(f"Health Score: {data.get('health_score', 'N/A')}/100")
        print(f"Total Issues Detected: {len(data.get('issues', []))}")
        print(f"{'━'*60}")
        
        print("\n📝 Executive Summary:")
        print(data.get('executive_summary', 'No summary generated.'))
        
        print(f"\n{'━'*60}")
        print("🚩 Top Priorities:")
        priorities = data.get('top_priorities', [])
        if priorities:
            for p in priorities:
                print(f"  - {p}")
        else:
            print("  No high-priority issues identified.")

        # Breakdown findings by agent
        issues = data.get('issues', [])
        agent_counts = {}
        for issue in issues:
            agent = issue.get('agent', 'Unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
        print(f"\n📊 Violation Breakdown by Agent:")
        if agent_counts:
            for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {agent:16} : {count} issues")
        else:
            print("  No issues found — your data is clean!")

        print(f"\n{'━'*60}")
        print("Stress test finished successfully.")

    except requests.exceptions.Timeout:
        print("❌ Error: Analysis timed out after 60 seconds.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_stress_test()
