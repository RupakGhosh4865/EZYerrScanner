"""
SmartAgent End-to-End Integration Test
Tests the full flow: connect → analyze → HITL → execute
Requires: WireMock running on :8082, FastAPI on :8000
"""
import requests
import json

BASE = "http://localhost:8000"


def run_full_flow():
    print("=== SMARTAGENT END-TO-END TEST (WireMock) ===\n")

    # ─── 1. Test connection ────────────────────────────────────────────────
    print("1. Testing connection to Smartsheet (WireMock)...")
    r = requests.get(f"{BASE}/api/analyze/connect", timeout=10)
    assert r.status_code == 200, f"Connect failed: {r.status_code} {r.text}"
    conn = r.json()
    print(f"   Mode: {conn['mode']}")
    print(f"   Sheets found: {len(conn['sheets'])}")
    assert len(conn["sheets"]) > 0, "No sheets returned"
    sheet_id = conn["sheets"][0]["id"]
    print(f"   Using sheet_id: {sheet_id}\n")

    # ─── 2. Start analysis (LangGraph) ────────────────────────────────────
    print("2. Starting analysis (LangGraph pipeline running)...")
    r = requests.post(f"{BASE}/api/analyze/start", json={"sheet_id": sheet_id}, timeout=60)
    assert r.status_code == 200, f"Analyze failed: {r.status_code} {r.text}"
    analysis = r.json()
    print(f"   Health Score:      {analysis['health_score']}/100")
    print(f"   Domain:            {analysis['domain']}")
    print(f"   Issues found:      {len(analysis['issues'])}")
    print(f"   Proposed actions:  {len(analysis['proposed_actions'])}")
    summary = analysis.get("executive_summary", "")
    print(f"\n   Executive summary:\n   {summary[:300]}")

    if analysis.get("top_priorities"):
        print("\n   Top priorities:")
        for p in analysis["top_priorities"][:3]:
            print(f"     • {p}")

    # ─── 3. Simulate HITL — approve only SAFE actions ─────────────────────
    safe_ids = [
        a["action_id"] for a in analysis["proposed_actions"]
        if a.get("risk_level") == "SAFE"
    ]
    print(f"\n3. HITL: Approving {len(safe_ids)} SAFE action(s) "
          f"out of {len(analysis['proposed_actions'])} total")

    # ─── 4. Execute approved actions ──────────────────────────────────────
    print("\n4. Executing approved actions against WireMock...")
    payload = {
        "sheet_id": sheet_id,
        "approved_action_ids": safe_ids,
        "proposed_actions": analysis["proposed_actions"],
        "column_map": analysis.get("column_map", {}),
        "issues": analysis["issues"],
        "health_score": analysis["health_score"],
        "sheet_name": analysis.get("sheet_name", "Test Sheet"),
    }
    r = requests.post(f"{BASE}/api/actions/execute", json=payload, timeout=30)
    assert r.status_code == 200, f"Execute failed: {r.status_code} {r.text}"
    execution = r.json()

    print(f"   Total executed:  {execution['total_executed']}")
    print(f"   Successful:      {execution['success_count']}")
    print(f"   Failed:          {execution['failed_count']}")
    print(f"   Audit sheet URL: {execution.get('audit_sheet_url') or 'N/A'}")

    if execution.get("executed_actions"):
        print("\n   Executed action details:")
        for ea in execution["executed_actions"][:3]:
            print(f"     [{ea['status'].upper()}] {ea['action_type']} (id={ea['action_id'][:8]}...)")

    # ─── Final summary ────────────────────────────────────────────────────
    print("\n" + "="*50)
    print("=== ALL 4 STEPS PASSED — Phase 3 Complete ===")
    print("="*50)
    print(f"\nSmartAgent analysed '{analysis.get('sheet_name', sheet_id)}'")
    print(f"  Health score:  {analysis['health_score']}/100")
    print(f"  Issues found:  {len(analysis['issues'])}")
    print(f"  Actions run:   {execution['total_executed']} ({execution['success_count']} succeeded)")
    print("\nRun: python scripts/wiremock_admin.py to see all WireMock requests received.")


if __name__ == "__main__":
    run_full_flow()
