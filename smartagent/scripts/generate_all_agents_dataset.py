"""
generate_all_agents_dataset.py
==============================
Generates a synthetic CSV designed to trigger *all* SmartAgent analyzers:

- duplicate_hunter: exact duplicates
- quality_auditor: missing/blank values
- logic_validator: invalid status + contradictions + due < start
- stale_detector: very old last_updated / overdue
- anomaly_detector: numeric outliers (cost >> budget, completion_pct > 100, etc.)

Output: scripts/all_agents_dataset.csv
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

COLUMNS = [
    "task_id",
    "task_name",
    "assigned_to",
    "department",
    "status",
    "priority",
    "start_date",
    "due_date",
    "budget_usd",
    "actual_cost_usd",
    "completion_pct",
    "subtask_count",
    "last_updated",
    "notes",
    "risk_flag",
    "sprint_id",
    "ticket_ref",
]

USERS = [
    "Alice Chen",
    "Bob Smith",
    "Charlie Davis",
    "Diana Prince",
    "Ethan Hunt",
    "Fiona Gallagher",
    "George Weasley",
    "Hannah Lee",
    "Ivan Drago",
    "Julia Roberts",
]

DEPTS = ["Engineering", "Marketing", "Design", "QA", "Operations", "Finance"]
VALID_STATUSES = ["Not Started", "In Progress", "Done", "Blocked", "Cancelled"]
VALID_PRIORITIES = ["High", "Medium", "Low"]


def fmt(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def rand_date(start: datetime, min_days: int, max_days: int) -> datetime:
    return start + timedelta(days=random.randint(min_days, max_days))


def base_rows(n: int) -> list[dict]:
    now = datetime.now()
    base = datetime(2024, 1, 1)
    rows: list[dict] = []

    for i in range(1, n + 1):
        tid = f"T-{2000 + i}"
        start = rand_date(base, i, i + 5)
        due = rand_date(start, 5, 30)
        budget = random.randint(1000, 20000)
        actual = int(budget * random.uniform(0.4, 1.1))
        dept = random.choice(DEPTS)
        status = random.choice(VALID_STATUSES)
        priority = random.choice(VALID_PRIORITIES)
        pct = (
            0
            if status == "Not Started"
            else 100
            if status == "Done"
            else random.randint(10, 90)
        )
        assigned = random.choice(USERS)
        subtasks = random.randint(1, 4)
        last_upd = rand_date(start, 0, max((due - start).days, 1))
        notes = (
            f"Milestone for {dept} initiative #{i}. "
            f"Requires sign-off from {assigned}. "
            f"Estimated effort: {random.randint(2,40)}h."
        )

        rows.append(
            {
                "task_id": tid,
                "task_name": f"Implementation Phase {i}",
                "assigned_to": assigned,
                "department": dept,
                "status": status,
                "priority": priority,
                "start_date": fmt(start),
                "due_date": fmt(due),
                "budget_usd": str(budget),
                "actual_cost_usd": str(actual),
                "completion_pct": str(pct),
                "subtask_count": str(subtasks),
                "last_updated": fmt(last_upd),
                "notes": notes,
                "risk_flag": random.choice(["Low", "Medium", "High", ""]),
                "sprint_id": f"SPR-{random.randint(1,12):02d}",
                "ticket_ref": f"JIRA-{random.randint(1000,9999)}",
            }
        )

    # ---- Seed problems for each agent ----

    # duplicates: exact duplicate rows (same across all columns)
    rows.append(rows[0].copy())
    rows.append(rows[1].copy())
    rows.append(rows[0].copy())

    # quality: missing values (None/blank)
    for idx in [5, 6, 7, 8, 9]:
        rows[idx]["risk_flag"] = ""
        rows[idx]["ticket_ref"] = ""
    rows[10]["assigned_to"] = ""
    rows[11]["task_name"] = "   "
    rows[12]["notes"] = ""

    # logic: invalid / contradictory
    # due < start
    s = datetime.strptime(rows[20]["start_date"], "%Y-%m-%d")
    rows[20]["due_date"] = fmt(s - timedelta(days=3))
    # completion 100 but not Done
    rows[21]["completion_pct"] = "100"
    rows[21]["status"] = "In Progress"
    # completion 0 but Done
    rows[22]["completion_pct"] = "0"
    rows[22]["status"] = "Done"
    # invalid status string
    rows[23]["status"] = "BLOCKED!"
    # negative budget
    rows[24]["budget_usd"] = "-5000"

    # stale: very old last_updated + overdue
    for idx in range(30, 38):
        rows[idx]["status"] = "In Progress"
        rows[idx]["last_updated"] = fmt(now - timedelta(days=240 + idx))
        rows[idx]["due_date"] = fmt(now - timedelta(days=30))

    # anomaly: big outliers
    rows[40]["budget_usd"] = "1500"
    rows[40]["actual_cost_usd"] = "12000"  # 8x budget
    rows[41]["completion_pct"] = "300"
    rows[42]["budget_usd"] = "0"
    rows[42]["actual_cost_usd"] = "5000"
    rows[43]["subtask_count"] = "50"
    rows[44]["completion_pct"] = "-20"

    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLUMNS})


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "all_agents_dataset.csv"
    rows = base_rows(120)
    write_csv(rows, out)
    print(f"Wrote {len(rows)} rows to {out}")

