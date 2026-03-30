"""
SmartAgent Graph Nodes
All LangGraph node functions for the SmartAgent pipeline.
"""
import datetime
import uuid
import os
from typing import Any
import pandas as pd

from graph.state import GraphState


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load Sheet (reads from WireMock or real Smartsheet)
# ─────────────────────────────────────────────────────────────────────────────

def load_sheet_node(state: GraphState) -> dict:
    """
    Loads the Smartsheet into state using SmartsheetReader (WireMock-backed).
    Sets: dataframe, metadata, raw_rows, column_map, sheet_name
    """
    from smartsheet_client.reader import SmartsheetReader

    reader = SmartsheetReader()

    try:
        df, metadata, raw_rows, column_map = reader.read_sheet(state["sheet_id"])
    except Exception as e:
        raise RuntimeError(f"Failed to load sheet from Smartsheet API: {e}")

    return {
        "dataframe": df.to_dict("records"),
        "metadata": metadata,
        "raw_rows": raw_rows,
        "column_map": column_map,
        "sheet_name": metadata["sheet_name"],
        "agent_statuses": [{
            "name": "sheet_loader",
            "status": "done",
            "duration_ms": 0,
            "issue_count": 0
        }]
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Schema Intelligence (detects domain, column types)
# ─────────────────────────────────────────────────────────────────────────────

def schema_node(state: GraphState) -> dict:
    """
    Analyses column names to determine sheet domain and types.
    """
    records = state.get("dataframe", [])
    columns = list(records[0].keys()) if records else list(state.get("column_map", {}).keys())

    columns_lower = [c.lower() for c in columns]

    # Simple heuristic domain detection
    if any(k in columns_lower for k in ["task", "status", "assignee", "owner", "due date", "priority"]):
        domain = "project_management"
    elif any(k in columns_lower for k in ["invoice", "amount", "revenue", "cost", "budget"]):
        domain = "finance"
    elif any(k in columns_lower for k in ["contact", "email", "phone", "company", "lead"]):
        domain = "crm"
    elif any(k in columns_lower for k in ["inventory", "sku", "quantity", "stock"]):
        domain = "inventory"
    else:
        domain = "general"

    # Detect date-like columns by name
    date_cols = [c for c in columns if any(k in c.lower() for k in ["date", "deadline", "due", "created", "modified"])]
    status_cols = [c for c in columns if "status" in c.lower()]

    date_pairs = []
    if len(date_cols) >= 2:
        date_pairs = [(date_cols[0], date_cols[1])]

    column_types = {}
    for col in columns:
        cl = col.lower()
        if any(k in cl for k in ["date", "deadline", "due"]):
            column_types[col] = "date"
        elif any(k in cl for k in ["status", "priority", "severity"]):
            column_types[col] = "picklist"
        elif any(k in cl for k in ["cost", "amount", "budget", "price", "qty", "quantity"]):
            column_types[col] = "numeric"
        else:
            column_types[col] = "text"

    primary_key_cols = [c for c in columns if "name" in c.lower() or "id" in c.lower() or "title" in c.lower()]

    return {
        "domain": domain,
        "column_types": column_types,
        "primary_key_cols": primary_key_cols[:2],
        "date_col_pairs": date_pairs,
        "agent_statuses": [{
            "name": "schema_intelligence",
            "status": "done",
            "duration_ms": 0,
            "issue_count": 0
        }]
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Supervisor (decides which agents to run)
# ─────────────────────────────────────────────────────────────────────────────

def supervisor_node(state: GraphState) -> dict:
    """
    Decides which specialist agents to activate based on domain.
    """
    domain = state.get("domain", "general")

    # Always run these core agents
    agents = ["duplicate_hunter", "quality_auditor", "logic_validator", "stale_detector"]

    return {
        "agents_to_run": agents,
        "agent_statuses": [{
            "name": "supervisor",
            "status": "done",
            "duration_ms": 0,
            "issue_count": 0
        }]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper: create a standard issue dict
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Specialist Agents
# ─────────────────────────────────────────────────────────────────────────────

def duplicate_node(state: GraphState) -> dict:
    """Detects duplicate rows in the sheet data."""
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    column_map = state.get("column_map", {})
    issues = []
    proposed_actions = []

    if len(records) < 2:
        return {"issues": [], "proposed_actions": state.get("proposed_actions", []),
                "agent_statuses": [{"name": "duplicate_hunter", "status": "done",
                                    "duration_ms": 0, "issue_count": 0}]}

    # Group rows by all-column hash
    seen: dict[str, list] = {}
    for i, rec in enumerate(records):
        key = str(sorted(rec.items()))
        seen.setdefault(key, []).append(i)

    dup_groups = {k: v for k, v in seen.items() if len(v) > 1}

    for group_rows in dup_groups.values():
        row_ids = [raw_rows[i]["__row_id__"] for i in group_rows if i < len(raw_rows)]
        row_nums = [raw_rows[i]["__row_number__"] for i in group_rows if i < len(raw_rows)]
        issue = _make_issue(
            agent="duplicate_hunter",
            title="Duplicate rows detected",
            description=f"Rows {row_nums} appear to be exact duplicates.",
            severity="HIGH",
            affected_rows=row_ids,
            affected_columns=list(records[0].keys()) if records else [],
            suggested_fix="Review and remove the duplicate entries.",
            confidence=0.95
        )
        issues.append(issue)

        # Propose a comment on the first duplicate row
        for row_id in row_ids[:1]:
            col_title = list(column_map.keys())[0] if column_map else ""
            col_id = list(column_map.values())[0] if column_map else 0
            proposed_actions.append(_make_action(
                action_type="add_comment",
                agent="duplicate_hunter",
                target_row_id=row_id,
                column_title=col_title,
                column_id=col_id,
                current_value="",
                proposed_value=f"[AI AUDIT] This row appears to be a duplicate of row(s) {row_nums}. Please review and remove if redundant.",
                reason="Duplicate row detected by duplicate_hunter agent.",
                severity="HIGH",
                risk_level="SAFE"
            ))

    existing_actions = state.get("proposed_actions", [])
    return {
        "issues": issues,
        "proposed_actions": existing_actions + proposed_actions,
        "agent_statuses": [{"name": "duplicate_hunter", "status": "done",
                            "duration_ms": 0, "issue_count": len(issues)}]
    }


def quality_node(state: GraphState) -> dict:
    """Detects missing / empty cell values."""
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    column_map = state.get("column_map", {})
    issues = []
    proposed_actions = []

    for i, rec in enumerate(records):
        empty_cols = [col for col, val in rec.items() if val is None or str(val).strip() == ""]
        if empty_cols and i < len(raw_rows):
            row_id = raw_rows[i]["__row_id__"]
            issue = _make_issue(
                agent="quality_auditor",
                title="Missing cell values",
                description=f"Row {raw_rows[i]['__row_number__']} has empty values in: {', '.join(empty_cols)}",
                severity="MEDIUM",
                affected_rows=[row_id],
                affected_columns=empty_cols,
                suggested_fix=f"Fill in the missing values for: {', '.join(empty_cols)}",
                confidence=0.85
            )
            issues.append(issue)
            # Propose a comment flag
            col_title = empty_cols[0]
            col_id = column_map.get(col_title, 0)
            proposed_actions.append(_make_action(
                action_type="add_comment",
                agent="quality_auditor",
                target_row_id=row_id,
                column_title=col_title,
                column_id=col_id,
                current_value="",
                proposed_value=f"[AI AUDIT] Missing value detected in column '{col_title}'. Please update.",
                reason="Empty cell detected by quality_auditor.",
                severity="MEDIUM",
                risk_level="SAFE"
            ))

    existing_actions = state.get("proposed_actions", [])
    return {
        "issues": issues,
        "proposed_actions": existing_actions + proposed_actions,
        "agent_statuses": [{"name": "quality_auditor", "status": "done",
                            "duration_ms": 0, "issue_count": len(issues)}]
    }


def logic_node(state: GraphState) -> dict:
    """Checks for logic/formula inconsistencies (status conflicts, etc.)."""
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    column_map = state.get("column_map", {})
    issues = []
    proposed_actions = []

    status_col = next((c for c in (records[0].keys() if records else []) if "status" in c.lower()), None)

    if status_col:
        valid_statuses = {"not started", "in progress", "complete", "done", "on hold",
                         "blocked", "open", "closed", "needs review", "cancelled"}
        for i, rec in enumerate(records):
            val = str(rec.get(status_col, "")).strip().lower()
            if val and val not in valid_statuses and i < len(raw_rows):
                row_id = raw_rows[i]["__row_id__"]
                col_id = column_map.get(status_col, 0)
                issue = _make_issue(
                    agent="logic_validator",
                    title="Unexpected status value",
                    description=f"Row {raw_rows[i]['__row_number__']} has unrecognised status '{rec.get(status_col)}'.",
                    severity="LOW",
                    affected_rows=[row_id],
                    affected_columns=[status_col],
                    suggested_fix=f"Update '{status_col}' to a valid value.",
                    confidence=0.75
                )
                issues.append(issue)
                proposed_actions.append(_make_action(
                    action_type="add_comment",
                    agent="logic_validator",
                    target_row_id=row_id,
                    column_title=status_col,
                    column_id=col_id,
                    current_value=str(rec.get(status_col, "")),
                    proposed_value=f"[AI AUDIT] Status value '{rec.get(status_col)}' may be invalid. Please review.",
                    reason="Unrecognised status value detected by logic_validator.",
                    severity="LOW",
                    risk_level="SAFE"
                ))

    existing_actions = state.get("proposed_actions", [])
    return {
        "issues": issues,
        "proposed_actions": existing_actions + proposed_actions,
        "agent_statuses": [{"name": "logic_validator", "status": "done",
                            "duration_ms": 0, "issue_count": len(issues)}]
    }


def stale_node(state: GraphState) -> dict:
    """Detects rows that haven't been updated recently."""
    records = state.get("dataframe", [])
    raw_rows = state.get("raw_rows", [])
    column_map = state.get("column_map", {})
    issues = []
    proposed_actions = []

    date_col = next((c for c in (records[0].keys() if records else [])
                     if any(k in c.lower() for k in ["date", "due", "deadline", "modified"])), None)

    if date_col:
        today = datetime.date.today()
        for i, rec in enumerate(records):
            val = str(rec.get(date_col, "")).strip()
            if not val:
                continue
            try:
                # Try parsing common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        row_date = datetime.datetime.strptime(val, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    continue  # unparseable date

                delta = (today - row_date).days
                if delta > 30 and i < len(raw_rows):
                    row_id = raw_rows[i]["__row_id__"]
                    col_id = column_map.get(date_col, 0)
                    issue = _make_issue(
                        agent="stale_detector",
                        title="Stale or overdue row",
                        description=f"Row {raw_rows[i]['__row_number__']} has '{date_col}' = {val} ({delta} days ago).",
                        severity="MEDIUM" if delta > 90 else "LOW",
                        affected_rows=[row_id],
                        affected_columns=[date_col],
                        suggested_fix=f"Review and update the '{date_col}' field or close this item.",
                        confidence=0.80
                    )
                    issues.append(issue)
                    proposed_actions.append(_make_action(
                        action_type="add_comment",
                        agent="stale_detector",
                        target_row_id=row_id,
                        column_title=date_col,
                        column_id=col_id,
                        current_value=val,
                        proposed_value=f"[AI AUDIT] This row appears stale ({delta} days since '{date_col}'). Please review.",
                        reason=f"Date field '{date_col}' is {delta} days old.",
                        severity="MEDIUM" if delta > 90 else "LOW",
                        risk_level="SAFE"
                    ))
            except Exception:
                pass

    existing_actions = state.get("proposed_actions", [])
    return {
        "issues": issues,
        "proposed_actions": existing_actions + proposed_actions,
        "agent_statuses": [{"name": "stale_detector", "status": "done",
                            "duration_ms": 0, "issue_count": len(issues)}]
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Aggregator (de-dupes proposed_actions, computes health score)
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_node(state: GraphState) -> dict:
    """Aggregates all issues and deduplicates action proposals."""
    issues = state.get("issues", [])
    proposed_actions = state.get("proposed_actions", [])

    # Deduplicate proposed actions by (action_type, target_row_id, column_title)
    seen_actions = set()
    deduped_actions = []
    for a in proposed_actions:
        key = (a.get("action_type"), a.get("target_row_id"), a.get("column_title"))
        if key not in seen_actions:
            seen_actions.add(key)
            deduped_actions.append(a)

    # Compute health score: start at 100, deduct per issue
    score = 100
    for issue in issues:
        sev = issue.get("severity", "LOW")
        score -= {"HIGH": 15, "MEDIUM": 8, "LOW": 3}.get(sev, 3)
    score = max(0, score)

    return {
        "proposed_actions": deduped_actions,
        "health_score": score,
        "agent_statuses": [{"name": "aggregator", "status": "done",
                            "duration_ms": 0, "issue_count": len(issues)}]
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Synthesizer (generates executive summary)
# ─────────────────────────────────────────────────────────────────────────────

def synthesizer_node(state: GraphState) -> dict:
    """Generates the executive summary and top priorities."""
    issues = state.get("issues", [])
    health_score = state.get("health_score", 100)
    domain = state.get("domain", "general")
    sheet_name = state.get("sheet_name", "Unknown Sheet")
    proposed_actions = state.get("proposed_actions", [])

    high_issues = [i for i in issues if i.get("severity") == "HIGH"]
    mid_issues = [i for i in issues if i.get("severity") == "MEDIUM"]

    summary = (
        f"SmartAgent analysed the '{sheet_name}' sheet (domain: {domain.replace('_', ' ')}). "
        f"Health Score: {health_score}/100. "
        f"Found {len(issues)} issue(s): {len(high_issues)} HIGH, {len(mid_issues)} MEDIUM. "
        f"{len(proposed_actions)} corrective action(s) proposed for human review."
    )

    if health_score >= 80:
        summary += " Overall sheet quality is GOOD."
    elif health_score >= 60:
        summary += " Sheet quality needs ATTENTION."
    else:
        summary += " Sheet quality is POOR — immediate action recommended."

    top_priorities = [
        f"[{i.get('severity')}] {i.get('title')} — {i.get('description', '')[:80]}"
        for i in sorted(issues, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.get("severity", "LOW"), 2))[:5]
    ]

    return {
        "executive_summary": summary,
        "top_priorities": top_priorities,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "agent_statuses": [{"name": "synthesizer", "status": "done",
                            "duration_ms": 0, "issue_count": 0}]
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTE ACTIONS NODE (called separately via /api/actions/execute)
# ─────────────────────────────────────────────────────────────────────────────

def execute_actions_node(state: dict) -> dict:
    """
    Runs only the approved actions against Smartsheet (WireMock or real).
    Called AFTER human approval — NOT part of the analysis graph.
    """
    from smartsheet_client.writer import SmartsheetWriter

    approved_ids = set(state.get("approved_action_ids", []))
    all_proposed = state.get("proposed_actions", [])
    to_execute = [a for a in all_proposed if a["action_id"] in approved_ids]

    if not to_execute:
        return {"executed_actions": [], "audit_sheet_url": ""}

    writer = SmartsheetWriter(
        sheet_id=state["sheet_id"],
        column_map=state.get("column_map", {})
    )

    executed = []
    audit_sheet_url = ""

    # Execute in safe-first order
    order = {"flag_cell": 0, "add_comment": 1, "update_status": 2,
             "update_cell_value": 3, "create_audit_sheet": 4}
    to_execute.sort(key=lambda a: order.get(a["action_type"], 99))

    for action in to_execute:
        try:
            result = {}
            atype = action["action_type"]

            if atype == "add_comment":
                result = writer.add_row_comment(
                    row_id=action["target_row_id"],
                    comment_text=action["proposed_value"]
                )

            elif atype == "flag_cell":
                result = writer.flag_cell(
                    row_id=action["target_row_id"],
                    column_title=action.get("column_title", ""),
                    note=action["proposed_value"]
                )

            elif atype in ("update_status", "update_cell_value"):
                result = writer.update_cell_value(
                    row_id=action["target_row_id"],
                    column_title=action.get("column_title", "Status"),
                    new_value=action["proposed_value"]
                )

            elif atype == "create_audit_sheet":
                result = writer.create_audit_sheet(
                    issues=state.get("issues", []),
                    health_score=state.get("health_score", 0),
                    source_sheet_name=state.get("sheet_name", "Sheet")
                )
                audit_sheet_url = result.get("sheet_url", "")

            executed.append({
                "action_id": action["action_id"],
                "action_type": atype,
                "status": result.get("status", "success"),
                "smartsheet_response": str(result),
                "executed_at": datetime.datetime.utcnow().isoformat()
            })

        except Exception as e:
            executed.append({
                "action_id": action["action_id"],
                "action_type": action.get("action_type", "unknown"),
                "status": "failed",
                "smartsheet_response": str(e),
                "executed_at": datetime.datetime.utcnow().isoformat()
            })

    return {
        "executed_actions": executed,
        "audit_sheet_url": audit_sheet_url
    }
