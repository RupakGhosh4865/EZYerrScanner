import pandas as pd
from datetime import datetime, timedelta
import random
import os

data = []
# Create 50 rows
for i in range(1, 51):
    data.append({
        "task_id": f"TSK-{100+i}",
        "task_name": f"Project Task {i}",
        "assignee": f"User {i%10}",
        "status": "In Progress" if i % 2 == 0 else "Completed",
        "priority": random.choice(["High", "Medium", "Low"]),
        "start_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": None,
        "budget": 5000 + (i * 100),
        "actual_cost": 4000 + (i * 90),
        "client_feedback": f"Looks good {i}" if i % 3 == 0 else "Needs changes",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "project_code": f"PRJ-{i%5}",
        "department": "Engineering",
        "completion_pct": 50
    })

# Embedded issues:
# - 4 exact duplicate rows
data.extend([data[0].copy(), data[0].copy(), data[0].copy(), data[0].copy()])

# - 3 near-duplicates
data[1]["assignee"] = "John Doe"
nd1 = data[1].copy()
nd1["task_id"] = "TSK-999"
nd1["assignee"] = "Jon Doe" # typo

data[2]["assignee"] = "Jane Smith"
nd2 = data[2].copy()
nd2["task_id"] = "TSK-998"
nd2["assignee"] = "Jane Smithe" # typo

data[3]["assignee"] = "Alice"
nd3 = data[3].copy()
nd3["task_id"] = "TSK-997"
nd3["assignee"] = "Alic" # typo
data.extend([nd1, nd2, nd3])

# - 1 column (client_feedback) with 65% null values
for i in range(35): data[i]["client_feedback"] = None

# - 1 column (completion_pct) with 30% null values
for i in range(15): data[i+20]["completion_pct"] = None

# - 5 rows where due_date is before start_date
for i in range(10, 15):
    data[i]["due_date"] = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

# - 6 rows with status="In Progress" but due_date 45+ days in the past
for i in range(25, 31):
    data[i]["status"] = "In Progress"
    data[i]["due_date"] = (datetime.now() - timedelta(days=50)).strftime("%Y-%m-%d")

# - 3 rows with negative budget values
for i in range(40, 43):
    data[i]["budget"] = -1000

# - Inconsistent status values
data[5]["status"] = "Done"
data[6]["status"] = "done"
data[7]["status"] = "DONE"
data[8]["status"] = "Completed"
data[9]["status"] = "complete"

# - 2 rows where actual_cost is 300%+ of budget
data[15]["budget"] = 1000
data[15]["actual_cost"] = 3500

data[16]["budget"] = 2000
data[16]["actual_cost"] = 7000

# - 4 rows with completion_pct > 100
for i in range(45, 49):
    data[i]["completion_pct"] = 150

# - Mixed date formats in start_date column
for i in range(18, 23):
    data[i]["start_date"] = (datetime.now() - timedelta(days=60)).strftime("%m/%d/%Y")

os.makedirs(r"d:\EZYerrScanner\backend\sample_data", exist_ok=True)
pd.DataFrame(data).to_csv(r"d:\EZYerrScanner\backend\sample_data\test_projects.csv", index=False)
