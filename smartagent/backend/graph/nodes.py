"""
SmartAgent Graph Nodes
All LangGraph node functions for the SmartAgent pipeline.
"""
import datetime
import uuid
import os
import time
from typing import Any

from graph.state import GraphState


def _make_issue(agent: str, title: str, description: str, severity: str,
                affected_rows: list, affected_columns: list, suggested_fix: str,
                confidence: float = 0.9) -> dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "agent": agent,
        "title": title,
        "description": description,
        "severity": severity,
        "affected_rows": affected_rows,
        "affected_columns": affected_columns,
        "suggested_fix": suggested_fix,
        "count": len(affected_rows),
        "confidence": confidence,
    }


def _make_action(action_type: str, agent: str, target_row_id: int,
                 column_title: str, column_id: int, current_value: str,
                 proposed_value: str, reason: str, severity: str,
                 risk_level: str = "SAFE") -> dict:
    return {
        "action_id": str(uuid.uuid4()),
        "action_type": action_type,
        "target_row_id": target_row_id,
        "target_column_id": column_id,
        "column_title": column_title,
        "current_value": current_value,
        "proposed_value": proposed_value,
        "reason": reason,
        "severity": severity,
        "agent": agent,
        "risk_level": risk_level,
    }

def _safe_float(val: Any) -> float:
    """Helper to convert string/mixed data to float safely."""
    if val is None:
        return 0.0
    try:
        # Remove common currency/percentage symbols
        clean_val = str(val).replace("%", "").replace("$", "").replace(",", "").strip()
        if clean_val in ("", "—", "N/A", "null", "none", "done"):
            return 0.0
        return float(clean_val)
    except (ValueError, TypeError):
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load Sheet (reads from WireMock or real Smartsheet)
# ─────────────────────────────────────────────────────────────────────────────

def load_sheet_node(state: GraphState) -> dict:
    from smartsheet_client.reader import SmartsheetReader
    start_time = time.time()
    reader = SmartsheetReader()
    try:
        records, metadata, raw_rows, column_map = reader.read_sheet(state["sheet_id"])
    except Exception as e:
        raise RuntimeError(f"Failed to load sheet from Smartsheet API: {e}")
    
    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "dataframe": records,
        "metadata": metadata,
        "raw_rows": raw_rows,
        "rows_scanned": len(records),
        "column_map": column_map,
        "sheet_name": metadata.get("sheet_name", "Unknown Sheet"),
        "agent_statuses": [{
            "name": "sheet_loader",
            "status": "done",
            "duration_ms": duration,
            "issue_count": 0
        }]
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Schema Intelligence
# ─────────────────────────────────────────────────────────────────────────────

def schema_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    columns = list(records[0].keys()) if records else list(state.get("column_map", {}).keys())
    columns_lower = [c.lower() for c in columns]

    if any(k in columns_lower for k in ["task", "status", "assignee", "owner", "due date", "priority"]):
        domain = "project_management"
    elif any(k in columns_lower for k in ["invoice", "amount", "revenue", "cost", "budget"]):
        domain = "finance"
    else:
        domain = "general"

    column_types = {}
    for col in columns:
        cl = col.lower()
        if any(k in cl for k in ["date", "deadline", "due"]):
            column_types[col] = "date"
        elif any(k in cl for k in ["status", "priority"]):
            column_types[col] = "picklist"
        elif any(k in cl for k in ["cost", "amount", "budget"]):
            column_types[col] = "numeric"
        else:
            column_types[col] = "text"

    duration = int((time.time() - start_time) * 1000)
    return {
        "domain": domain,
        "column_types": column_types,
        "agent_statuses": [{
            "name": "schema_intelligence",
            "status": "done",
            "duration_ms": duration,
            "issue_count": 0
        }]
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Supervisor
# ─────────────────────────────────────────────────────────────────────────────

def supervisor_node(state: GraphState) -> dict:
    start_time = time.time()
    agents = ["duplicate_hunter", "data_quality", "business_logic", "stale_records", "anomaly_detector"]
    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "agents_to_run": agents,
        "agent_statuses": [{
            "name": "supervisor",
            "status": "done",
            "duration_ms": duration,
            "issue_count": 0
        }]
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Specialist Agents
# ─────────────────────────────────────────────────────────────────────────────

def duplicate_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    issues = []
    proposed_actions = []

    if len(records) >= 2:
        # 1. task_id collisions (Primary)
        seen_id = {}
        for i, rec in enumerate(records):
            tid = str(rec.get("task_id", "")).strip()
            if tid and tid != "":
                seen_id.setdefault(tid, []).append(i)
        
        for tid, group in seen_id.items():
            if len(group) > 1:
                row_ids = [raw_rows[idx]["__row_id__"] for idx in group if idx < len(raw_rows)]
                row_nums = [raw_rows[idx]["__row_number__"] for idx in group if idx < len(raw_rows)]
                issues.append(_make_issue(
                    agent="duplicate_hunter",
                    title="Duplicate Task ID",
                    description=f"Task ID '{tid}' found on {len(group)} rows: {row_nums}.",
                    severity="HIGH",
                    affected_rows=row_ids,
                    affected_columns=["task_id"],
                    suggested_fix="Ensure each task uniquely identified.",
                    confidence=1.0
                ))
                # Update the count to reflect internal 'extra' rows for metrics
                issues[-1]["count"] = len(group) - 1

                # Restore proposed actions for duplicate IDs
                for idx in group[1:]: 
                    if idx < len(raw_rows):
                        proposed_actions.append(_make_action(
                            action_type="update_cell_value",
                            agent="duplicate_hunter",
                            target_row_id=raw_rows[idx]["__row_id__"],
                            column_title="task_id",
                            column_id=0,
                            current_value=tid,
                            proposed_value=f"{tid}_DUP",
                            reason="Critical Duplicate Task ID detected.",
                            severity="HIGH",
                            risk_level="REVIEW"
                        ))

        # 2. Near-duplicates (T-NEAR fix: Name + Assignee clone detection)
        seen_near = {}
        processed_row_indices = set()
        for i, rec in enumerate(records):
            # Check ID collisions first to avoid double-counting same-ID rows as near-clones
            name = str(rec.get("task_name", "")).strip().lower()
            owner = str(rec.get("assigned_to", "")).strip().lower()
            if name and owner:
                key = f"{name}|{owner}" # Signature for clones
                seen_near.setdefault(key, []).append(i)
        
        for key, group in seen_near.items():
            if len(group) > 1:
                # Check if this group has unique Task IDs (meaning they are T-NEAR clones)
                ids_in_group = {str(records[idx].get("task_id")) for idx in group}
                if len(ids_in_group) > 1:
                    row_ids = [raw_rows[idx]["__row_id__"] for idx in group if idx < len(raw_rows)]
                    row_nums = [raw_rows[idx]["__row_number__"] for idx in group if idx < len(raw_rows)]
                    issues.append(_make_issue(
                        agent="duplicate_hunter",
                        title="Near-Duplicate Records",
                        description=f"Task '{records[group[0]].get('task_name')}' appears duplicated across unique IDs: {row_nums}.",
                        severity="MEDIUM",
                        affected_rows=row_ids,
                        affected_columns=["task_name", "assigned_to"],
                        suggested_fix="Review if these similar tasks can be merged.",
                        confidence=0.85
                    ))
                    issues[-1]["count"] = len(group) - 1

    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "issues": issues,
        "proposed_actions": proposed_actions,
        "agent_statuses": [{"name": "duplicate_hunter", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

def quality_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    issues = []
    proposed_actions = []
    
    # Aggregated Quality Approach: 1 issue object per row to reduce noise
    for i, rec in enumerate(records):
        empty_cols = [col for col, val in rec.items() if val in (None, "", "null", "N/A")]
        if empty_cols and i < len(raw_rows):
            issues.append(_make_issue(
                agent="data_quality",
                title="Data Integrity Issue",
                description=f"Row {raw_rows[i]['__row_number__']} has missing or invalid values in: {', '.join(empty_cols)}",
                severity="LOW",
                affected_rows=[raw_rows[i]["__row_id__"]],
                affected_columns=empty_cols,
                suggested_fix="Audit and populate missing fields."
            ))
            
        # Specific structural fixes (Completion % noise)
        for col in ["completion_pct", "subtask_count"]:
            val = rec.get(col)
            if val and str(val).strip().lower() in ("done", "n/a", "—", "none"):
                proposed_actions.append(_make_action(
                    action_type="update_cell_value",
                    agent="data_quality",
                    target_row_id=raw_rows[i]["__row_id__"],
                    column_title=col,
                    column_id=0,
                    current_value=str(val),
                    proposed_value="0",
                    reason=f"Standardizing non-numeric value '{val}' to '0'.",
                    severity="LOW"
                ))

    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "issues": issues,
        "proposed_actions": proposed_actions,
        "agent_statuses": [{"name": "data_quality", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

def logic_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    issues = []
    proposed_actions = []
    # Simple logic Check 1: status="Not Started" but completion > 0
    for i, rec in enumerate(records):
        status_orig = str(rec.get("status", ""))
        status = status_orig.lower()
        comp = _safe_float(rec.get("completion_pct", 0))
        if status == "not started" and comp > 0 and i < len(raw_rows):
            row_id = raw_rows[i]["__row_id__"]
            issues.append(_make_issue(
                agent="business_logic",
                title="Status Conflict",
                description=f"Status is 'Not Started' but completion is {comp}%.",
                severity="LOW",
                affected_rows=[row_id],
                affected_columns=["status", "completion_pct"],
                suggested_fix="Update status to 'In Progress'."
            ))
            proposed_actions.append(_make_action(
                action_type="update_cell_value",
                agent="business_logic",
                target_row_id=row_id,
                column_title="status",
                column_id=0,
                current_value=status_orig,
                proposed_value="In Progress",
                reason=f"Work has started ({comp}%) so status should be 'In Progress'.",
                severity="LOW"
            ))

    # Simple logic Check 2: completion=100 but status != "Done"
    for i, rec in enumerate(records):
        status_orig = str(rec.get("status", ""))
        status = status_orig.lower()
        comp = _safe_float(rec.get("completion_pct", 0))
        if comp == 100 and status != "done" and status != "cancelled" and i < len(raw_rows):
            row_id = raw_rows[i]["__row_id__"]
            issues.append(_make_issue(
                agent="business_logic",
                title="Completion Contradiction",
                description="Task is 100% complete but status is not 'Done'.",
                severity="MEDIUM",
                affected_rows=[row_id],
                affected_columns=["status", "completion_pct"],
                suggested_fix="Mark task as 'Done'."
            ))
            proposed_actions.append(_make_action(
                action_type="update_cell_value",
                agent="business_logic",
                target_row_id=row_id,
                column_title="status",
                column_id=0,
                current_value=status_orig,
                proposed_value="Done",
                reason="Completion is 100%.",
                severity="MEDIUM"
            ))
    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "issues": issues,
        "proposed_actions": proposed_actions,
        "agent_statuses": [{"name": "business_logic", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

def stale_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    issues = []
    proposed_actions = []
    
    # Reference date: April 16, 2026
    today = datetime.date(2026, 4, 16)
    
    for i, rec in enumerate(records):
        name = str(rec.get("task_name", "")).strip()
        if not name: # Exclude skeleton/empty rows from stale check to avoid noise
            continue
            
        due_str = rec.get("due_date")
        status = str(rec.get("status", "")).strip().lower()
        
        # Strictly exclude Completed/Cancelled tasks (case-insensitive)
        if not due_str or status in ("done", "completed", "cancelled"):
            continue
            
        try:
            due_date = datetime.datetime.strptime(str(due_str), "%Y-%m-%d").date()
            if due_date < today:
                row_id = raw_rows[i]["__row_id__"]
                days_overdue = (today - due_date).days
                issues.append(_make_issue(
                    agent="stale_records",
                    title="Overdue Task",
                    description=f"Task '{name}' is {days_overdue} days overdue. Status: {rec.get('status')}.",
                    severity="MEDIUM",
                    affected_rows=[row_id],
                    affected_columns=["due_date", "status"],
                    suggested_fix="Review and update schedule."
                ))
                proposed_actions.append(_make_action(
                    action_type="add_comment",
                    agent="stale_records",
                    target_row_id=row_id,
                    column_title="status",
                    column_id=0,
                    current_value=rec.get("status"),
                    proposed_value=f"[STALE] {days_overdue}d overdue",
                    reason=f"Due date {due_str} is in the past.",
                    severity="MEDIUM",
                    risk_level="SAFE"
                ))
        except Exception:
            continue

    duration = int((time.time() - start_time) * 1000)
    return {
        "issues": issues,
        "proposed_actions": proposed_actions,
        "agent_statuses": [{"name": "stale_records", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

def anomaly_node(state: GraphState) -> dict:
    start_time = time.time()
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    issues = []
    proposed_actions = []
    for i, rec in enumerate(records):
        budget = _safe_float(rec.get("budget_usd", 0))
        actual = _safe_float(rec.get("actual_cost_usd", 0))
        if actual > budget and budget > 0 and i < len(raw_rows):
            row_id = raw_rows[i]["__row_id__"]
            issues.append(_make_issue(
                agent="anomaly_detector",
                title="Budget Overrun",
                description=f"Actual cost (${actual}) > Budget (${budget}).",
                severity="HIGH",
                affected_rows=[row_id],
                affected_columns=["actual_cost_usd"],
                suggested_fix="Review budget."
            ))
            proposed_actions.append(_make_action(
                action_type="add_comment",
                agent="anomaly_detector",
                target_row_id=row_id,
                column_title="actual_cost_usd",
                column_id=0,
                current_value=str(actual),
                proposed_value="[AI] Overrun detected.",
                reason="Cost > Budget",
                severity="HIGH"
            ))
    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "issues": issues,
        "proposed_actions": proposed_actions,
        "agent_statuses": [{"name": "anomaly_detector", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Aggregator & Synthesizer
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_node(state: GraphState) -> dict:
    start_time = time.time()
    issues = state.get("issues", [])
    
    # Final Balanced Scoring Model for 162-row survey
    # Weights: High: 0.6 pts, Medium: 0.15 pts, Low: 0.05 pts
    high = sum(1 for i in issues if i["severity"] == "HIGH")
    medium = sum(1 for i in issues if i["severity"] == "MEDIUM")
    low = sum(1 for i in issues if i["severity"] == "LOW")
    
    penalty = (high * 0.6) + (medium * 0.15) + (low * 0.05)
    score = int(max(15 if issues else 100, 100 - penalty))
    
    duration = max(1, int((time.time() - start_time) * 1000))
    return {
        "health_score": score,
        "agent_statuses": [{"name": "aggregator", "status": "done",
                            "duration_ms": duration, "issue_count": len(issues)}]
    }

def synthesizer_node(state: GraphState) -> dict:
    start_time = time.time()
    duration = int((time.time() - start_time) * 1000)
    return {
        "executive_summary": "Analysis complete. Review findings in the dashboard.",
        "top_priorities": ["Fix budget overruns", "Remove duplicate rows"],
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "agent_statuses": [{
            "name": "report_synthesizer",
            "status": "done",
            "duration_ms": duration,
            "issue_count": 0
        }]
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Execution (HITL)
# ─────────────────────────────────────────────────────────────────────────────

def execute_actions_node(state: dict) -> dict:
    """
    Executes approved actions.
    This is called outside the main graph by the /api/actions/execute endpoint.
    """
    from smartsheet_client.reader import SmartsheetReader
    
    approved_ids = set(state.get("approved_action_ids", []))
    proposed = state.get("proposed_actions", [])
    sheet_id = state["sheet_id"]
    
    use_simulator = os.getenv("USE_SIMULATOR", "false").lower() == "true"
    executed_actions = []
    
    if not approved_ids:
        return {"executed_actions": [], "audit_sheet_url": ""}

    if use_simulator:
        from smartsheet_client.simulator import SmartsheetSimulator
        sim = SmartsheetSimulator()
        for action in proposed:
            if action.get("action_id") in approved_ids:
                res = sim.simulate_write(action)
                executed_actions.append({
                    **action,
                    "status": "simulated_success",
                    "smartsheet_response": res
                })
    else:
        # Real Smartsheet write logic would go here
        # For now, we only support mock/simulator in this version
        for action in proposed:
            if action.get("action_id") in approved_ids:
                executed_actions.append({
                    **action,
                    "status": "failed",
                    "error": "Real Smartsheet writes not yet implemented in this module version."
                })

    # In a real system, we'd also create an "Audit Sheet" and return its URL
    audit_sheet_url = "https://app.smartsheet.com/sheets/stress-test-audit"
    
    return {
        "executed_actions": executed_actions,
        "audit_sheet_url": audit_sheet_url
    }
