"""
multi_agent_test_dataset.py
===========================
A rich, 162-row synthetic dataset engineered to stress-test every agent
in the Neural Agent Interaction Matrix.
No-Pandas Version (uses standard csv library for environment compatibility).
"""

import csv
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict

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

# ── build base 150 rows ──────────────────────────────────────────────────────
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
# TRAIT INJECTIONS (Must run after base loop to avoid being overwritten)
# =============================================================================

# Bug 4 Fix — Quality Specialist Traps (Strings in numeric columns)
rows[10]["budget_usd"]      = "N/A"    # T-2011
rows[11]["completion_pct"]  = "done"   # T-2012
rows[12]["subtask_count"]   = "—"      # T-2013
rows[13]["actual_cost_usd"] = ""       # T-2014
rows[14]["risk_flag"]       = 99       # T-2015

for idx in [30, 31, 32]: # T-2031-33
    rows[idx]["task_name"]   = "   "
    rows[idx]["assigned_to"] = ""

# Agent 3 — Logic Validation Traps
# Forward Contradiction (PCT=100 but In Progress)
for idx in [50, 51, 52]: # T-2051-53
    rows[idx]["status"] = "In Progress"
    rows[idx]["completion_pct"] = 100 

# Reverse Contradiction (Status=Done but PCT=0)
for idx in [53, 54]: # T-2054-55
    rows[idx]["status"] = "Done"
    rows[idx]["completion_pct"] = 0

# Due Before Start
for idx in [40, 41, 42, 43, 44]: # T-2041-45
    s = datetime.strptime(rows[idx]["start_date"], "%Y-%m-%d")
    rows[idx]["due_date"] = fmt(s - timedelta(days=random.randint(1, 7)))

# Negative Values
for idx in [60, 61, 62]: # T-2061-63
    rows[idx]["budget_usd"] = -5000 
for idx in [74, 75]:     # T-2075-76
    rows[idx]["subtask_count"] = -3

# Overspends / Under-budgets
for idx in [63, 64, 65]: # T-2064-66
    rows[idx]["budget_usd"]      = 1000
    rows[idx]["actual_cost_usd"] = 5500

# Invalid Enums
for idx in [70, 71]:     # T-2071-72
    rows[idx]["priority"] = "Critical"
for idx in [72, 73]:     # T-2073-74
    rows[idx]["status"] = random.choice(["DONE", "in progress", "BLOCKED!"])

# Agent 4 — Anomaly AI Traps
rows[80]["actual_cost_usd"] = rows[80]["budget_usd"] * 8   # T-2081
rows[81]["completion_pct"]  = 300                          # T-2082
rows[82]["budget_usd"]      = 0                            # T-2083
rows[82]["actual_cost_usd"] = 5000
rows[83]["subtask_count"]   = 50                           # T-2084
rows[84]["completion_pct"]  = -20                          # T-2085
rows[85]["budget_usd"]      = 500000                       # T-2086
rows[85]["department"]      = "Finance"
rows[86]["due_date"]        = rows[86]["start_date"]       # T-2087

# Agent 5 — Stale Detector Traps
for idx in range(90, 105): # T-2091-2105
    rows[idx]["status"]       = "In Progress"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=random.randint(181, 400)))
    rows[idx]["due_date"]     = fmt(NOW - timedelta(days=10))

for idx in range(105, 113): # T-2106-2113
    rows[idx]["status"]       = "Not Started"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=random.randint(365, 600)))
    rows[idx]["completion_pct"] = 0

# Stale Detector Traps: Blocked rows (60-130 days stale)
# Fixing T-2114 to T-2118 as requested
for idx, offset in zip(range(113, 118), [75, 101, 143, 88, 120]):
    rows[idx]["status"]       = "Blocked"
    rows[idx]["last_updated"] = fmt(NOW - timedelta(days=offset))
    rows[idx]["notes"]        = ""

# =============================================================================
# AGENT 1 — DUPLICATE SCAN (Appended cases)
# =============================================================================
# Bug 1 Fix — Source-mapping for cloned names (Must match source exactly)
source_map_data = {
    "T-2001": rows[0],
    "T-2002": rows[1],
    "T-2003": rows[2],
    "T-2004": rows[3]
}
for src_id in ["T-2001", "T-2001", "T-2002", "T-2003", "T-2003", "T-2004"]:
    source_row = source_map_data[src_id]
    clone = dict(source_row)
    clone["task_name"] = source_row["task_name"] # Force exact name match
    clone["last_updated"] = fmt(NOW - timedelta(days=random.randint(1,10)))
    rows.append(clone)

# Near-Duplicates
for i in range(6):
    near = dict(rows[i*5]) # T-2001, T-2006, etc.
    near["task_id"] = f"T-NEAR-{i+1}"
    rows.append(near)

# Final Cleanup (Randomizing non-audit rows to add noise)
for idx in random.sample(range(0, 150), 40):
    if idx > 15: # Leave specific audit targets alone
        rows[idx]["risk_flag"]  = None
        rows[idx]["ticket_ref"] = None

# =============================================================================
# EXPORT
# =============================================================================
if __name__ == "__main__":
    fieldnames = list(rows[0].keys())
    
    paths = ["all_agents_dataset.csv", "../backend/all_agents_dataset.csv"]
    for p in paths:
        try:
            # Ensure the directory exists
            dir_name = os.path.dirname(p)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
                
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Exported to {p}")
        except Exception as e:
            print(f"Failed to export to {p}: {e}")

    print(f"\nTotal rows generated: {len(rows)}")
    print("Done. All audit scenarios are correctly seeded.")
