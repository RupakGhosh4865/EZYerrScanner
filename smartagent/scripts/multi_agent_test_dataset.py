"""
multi_agent_test_dataset.py
===========================
A rich, 150-row synthetic dataset engineered to stress-test every agent
in the Neural Agent Interaction Matrix:

  Agent                 | What's seeded
  ----------------------|-----------------------------------------------------
  DUPLICATE SCAN        | 12 exact & near-duplicate rows (same ID or same
                        | name+dept+date triple)
  QUALITY CHECK         | 3 columns with >60% nulls, wrong-type values,
                        | blank strings stored as "N/A" or "—"
  LOGIC VALIDATOR       | Due < Start, Completion=100 but Status≠Done,
                        | negative budget, cost > budget*3, Priority="Critical"
                        | (not in allowed list)
  ANOMALY AI            | 6 statistical outliers: cost 8x budget, completion
                        | 300%, budget $0, single task with 9 subtasks
  STALE DETECTOR        | 15 rows untouched for >180 days, 8 tasks "In Progress"
                        | with last_updated >90 days ago
  AI SUMMARIZER         | Rich text in Notes column, multi-department spread,
                        | varied priorities — enough signal for a real summary
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

random.seed(42)  # reproducible

# ── helpers ──────────────────────────────────────────────────────────────────
NOW        = datetime.now()
BASE_DATE  = datetime(2024, 1, 1)

USERS   = ["Alice Chen", "Bob Smith", "Charlie Davis", "Diana Prince",
           "Ethan Hunt", "Fiona Gallagher", "George Weasley", "Hannah Lee",
           "Ivan Drago", "Julia Roberts"]
DEPTS   = ["Engineering", "Marketing", "Design", "QA", "Operations", "Finance"]
VALID_STATUSES   = ["Not Started", "In Progress", "Done", "Blocked", "Cancelled"]
VALID_PRIORITIES = ["High", "Medium", "Low"]

def rand_date(start: datetime, min_days: int, max_days: int) -> datetime:
    return start + timedelta(days=random.randint(min_days, max_days))

def fmt(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

# ── build rows ────────────────────────────────────────────────────────────────
rows: List[Dict] = []

for i in range(1, 151):
    uid        = f"T-{2000 + i}"
    start      = rand_date(BASE_DATE, i, i + 5)
    due        = rand_date(start, 5, 30)
    budget     = random.randint(1000, 20000)
    actual     = int(budget * random.uniform(0.4, 1.1))
    dept       = random.choice(DEPTS)
    status     = random.choice(VALID_STATUSES)
    priority   = random.choice(VALID_PRIORITIES)
    pct        = (0 if status == "Not Started" else
                  100 if status == "Done" else
                  random.randint(10, 90))
    assigned   = random.choice(USERS)
    subtasks   = random.randint(1, 4)
    last_upd   = rand_date(start, 0, (due - start).days or 1)
    notes      = (f"Milestone for {dept} initiative #{i}. "
                  f"Requires sign-off from {assigned}. "
                  f"Estimated effort: {random.randint(2,40)}h." )

    rows.append({
        "task_id":        uid,
        "task_name":      f"Implementation Phase {i}",
        "assigned_to":    assigned,
        "department":     dept,
        "status":         status,
        "priority":       priority,
        "start_date":     fmt(start),
        "due_date":       fmt(due),
        "budget_usd":     budget,
        "actual_cost_usd":actual,
        "completion_pct": pct,
        "subtask_count":  subtasks,
        "last_updated":   fmt(last_upd),
        "notes":          notes,
        "risk_flag":      random.choice(["Low", "Medium", "High", None]),
        "sprint_id":      f"SPR-{random.randint(1,12):02d}",
        "ticket_ref":     f"JIRA-{random.randint(1000,9999)}",
    })

# =============================================================================
# AGENT 1 — DUPLICATE SCAN
# 6 exact task_id duplicates  +  6 near-dupes (same name+dept, different ID)
# =============================================================================
# 1a. Exact ID duplicates (rows 151-156 clone IDs from rows 1-3)
for i, src_id in enumerate(["T-2001", "T-2001", "T-2002", "T-2003", "T-2003", "T-2004"]):
    clone = rows[0].copy()
    clone["task_id"]    = src_id
    clone["task_name"]  = f"Implementation Phase {i+1}"   # same name too
    clone["last_updated"] = fmt(NOW - timedelta(days=random.randint(1,10)))
    rows.append(clone)

# 1b. Near-duplicates: same task_name + dept, different IDs
for i in range(6):
    near = rows[i*5].copy()
    near["task_id"]   = f"T-NEAR-{i+1}"
    near["task_name"] = rows[i*5]["task_name"]          # same name
    near["department"]= rows[i*5]["department"]         # same dept
    near["start_date"]= rows[i*5]["start_date"]         # same start
    rows.append(near)

# =============================================================================
# AGENT 2 — QUALITY CHECK
# Null storms, blank strings, wrong types
# =============================================================================
# 2a. 60% of rows 20-80 get None notes (column quality issue)
for idx in random.sample(range(20, 80), 37):
    rows[idx]["notes"] = None

# 2b. Wrong-type values
rows[10]["budget_usd"]     = "N/A"          # string in numeric col
rows[11]["completion_pct"] = "done"         # string in numeric col
rows[12]["subtask_count"]  = "—"            # dash as null
rows[13]["actual_cost_usd"]= ""             # empty string
rows[14]["risk_flag"]      = 99             # int in enum col

# 2c. Blank/whitespace-only strings
for idx in [30, 31, 32]:
    rows[idx]["task_name"]  = "   "
    rows[idx]["assigned_to"]= ""

# 2d. Null-storm columns: risk_flag and ticket_ref with 65% nulls
for idx in random.sample(range(0, 150), 98):
    rows[idx]["risk_flag"]  = None
for idx in random.sample(range(0, 150), 97):
    rows[idx]["ticket_ref"] = None

# =============================================================================
# AGENT 3 — LOGIC VALIDATOR
# =============================================================================
# 3a. Due Date < Start Date
for idx in [40, 41, 42, 43, 44]:
    s = datetime.strptime(rows[idx]["start_date"], "%Y-%m-%d")
    rows[idx]["due_date"] = fmt(s - timedelta(days=random.randint(1, 7)))

# 3b. Completion = 100 but Status ≠ "Done"
for idx in [50, 51, 52]:
    rows[idx]["completion_pct"] = 100
    rows[idx]["status"]         = "In Progress"   # contradiction

# 3c. Completion = 0 but Status = "Done"
for idx in [53, 54]:
    rows[idx]["completion_pct"] = 0
    rows[idx]["status"]         = "Done"           # contradiction

# 3d. Negative budget
for idx in [60, 61, 62]:
    rows[idx]["budget_usd"] = -abs(rows[idx]["budget_usd"])

# 3e. Actual cost > 3× budget
for idx in [63, 64, 65]:
    rows[idx]["budget_usd"]     = 1000
    rows[idx]["actual_cost_usd"]= random.randint(4000, 6000)

# 3f. Invalid priority value (not in allowed list)
for idx in [70, 71]:
    rows[idx]["priority"] = "Critical"   # not in VALID_PRIORITIES

# 3g. Invalid status value
for idx in [72, 73]:
    rows[idx]["status"] = random.choice(["done", "DONE", "in progress", "BLOCKED!"])

# 3h. Subtask count < 0
for idx in [74, 75]:
    rows[idx]["subtask_count"] = -3

# =============================================================================
# AGENT 4 — ANOMALY AI  (statistical outliers)
# =============================================================================
# 4a. Cost 8× budget
rows[80]["budget_usd"]      = 1500
rows[80]["actual_cost_usd"] = 12000    # 8x

# 4b. Completion % = 300
rows[81]["completion_pct"]  = 300

# 4c. Budget = $0
rows[82]["budget_usd"]      = 0
rows[82]["actual_cost_usd"] = 5000

# 4d. Subtask count = 50 (way above normal range 1-4)
rows[83]["subtask_count"]   = 50

# 4e. Completion % = -20
rows[84]["completion_pct"]  = -20

# 4f. Single task burns 90% of department budget (needs context — flagged by AI)
rows[85]["budget_usd"]      = 500000
rows[85]["department"]      = "Finance"
rows[85]["notes"]           = "Approved by CFO. Special capital expenditure Q4."

# 4g. Duration = 0 days (start == due)
rows[86]["due_date"]        = rows[86]["start_date"]

# =============================================================================
# AGENT 5 — STALE DETECTOR
# =============================================================================
# 5a. last_updated > 180 days ago, still "In Progress"
for idx in range(90, 105):
    rows[idx]["status"]       = "In Progress"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=random.randint(181, 400)))
    rows[idx]["due_date"]     = fmt(NOW - timedelta(days=random.randint(10, 90)))

# 5b. last_updated > 365 days ago, status "Not Started" (zombie tasks)
for idx in range(105, 113):
    rows[idx]["status"]       = "Not Started"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=random.randint(365, 600)))
    rows[idx]["completion_pct"] = 0

# 5c. "Blocked" for > 60 days with no notes update
for idx in range(113, 118):
    rows[idx]["status"]       = "Blocked"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=random.randint(61, 150)))
    rows[idx]["notes"]        = None   # no update either

# =============================================================================
# BUILD DATAFRAME & SUMMARY
# =============================================================================
df = pd.DataFrame(rows)

AGENT_SUMMARY = {
    "DUPLICATE_SCAN": {
        "exact_id_dupes":    6,
        "near_dupes":        6,
        "affected_rows":     "151-162",
        "detection_columns": ["task_id", "task_name", "department", "start_date"],
    },
    "QUALITY_CHECK": {
        "null_storm_columns":    ["notes (>60%)", "risk_flag (>65%)", "ticket_ref (>65%)"],
        "wrong_type_rows":       [10, 11, 12, 13, 14],
        "blank_string_rows":     [30, 31, 32],
        "total_quality_issues":  "~250 cells",
    },
    "LOGIC_VALIDATOR": {
        "due_before_start":              [40,41,42,43,44],
        "pct100_not_done":               [50,51,52],
        "pct0_but_done":                 [53,54],
        "negative_budget":               [60,61,62],
        "cost_over_3x_budget":           [63,64,65],
        "invalid_priority":              [70,71],
        "invalid_status_casing":         [72,73],
        "negative_subtask_count":        [74,75],
    },
    "ANOMALY_AI": {
        "cost_8x_budget":       80,
        "completion_300pct":    81,
        "budget_zero":          82,
        "subtasks_50":          83,
        "completion_negative":  84,
        "whale_budget_500k":    85,
        "zero_day_duration":    86,
    },
    "STALE_DETECTOR": {
        "in_progress_180plus_days_stale":  list(range(90,105)),
        "zombie_not_started_365plus":      list(range(105,113)),
        "blocked_60plus_no_notes":         list(range(113,118)),
    },
    "AI_SUMMARIZER": {
        "total_rows":       len(df),
        "departments":      df["department"].nunique(),
        "status_breakdown": df["status"].value_counts().to_dict(),
        "priority_breakdown": df["priority"].value_counts().to_dict(),
        "avg_completion":   round(pd.to_numeric(df["completion_pct"], errors="coerce").mean(), 1),
        "total_budget":     pd.to_numeric(df["budget_usd"], errors="coerce").sum(),
        "date_range":       f"{df['start_date'].min()} → {df['due_date'].max()}",
    },
}

if __name__ == "__main__":
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}\n")
    for agent, info in AGENT_SUMMARY.items():
        print(f"{'─'*60}")
        print(f"  {agent}")
        for k, v in info.items():
            print(f"    {k}: {v}")
    print(f"\n{'─'*60}")
    print(f"Total rows: {len(df)}  |  Columns: {len(df.columns)}")
    print("Exporting with: df.to_csv('q2_tracker.csv', index=False)")
    df.to_csv("q2_tracker.csv", index=False)
