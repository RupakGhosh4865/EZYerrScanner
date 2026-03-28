from typing import TypedDict, Annotated, Any
import operator
import pandas as pd

class AgentStatus(TypedDict):
    name: str
    status: str          # "pending" | "running" | "done" | "skipped"
    duration_ms: int
    issue_count: int

class Issue(TypedDict):
    id: str
    agent: str
    title: str
    description: str
    severity: str        # "HIGH" | "MEDIUM" | "LOW"
    affected_rows: list[int]
    affected_columns: list[str]
    suggested_fix: str
    count: int
    confidence: float    # 0.0 - 1.0 (how confident the AI is)

class GraphState(TypedDict):
    # Input
    file_bytes: bytes
    filename: str
    
    # Parsed data (set by file_parser, passed through graph)
    dataframe: Any                    # pd.DataFrame serialized as dict
    metadata: dict                    # {rows, cols, filename, size_kb}
    
    # Schema intelligence output
    domain: str                       # "project_management" | "hr" | "finance" | "generic"
    column_types: dict                # {col_name: "date"|"id"|"status"|"numeric"|"text"}
    primary_key_cols: list[str]
    date_col_pairs: list[tuple]       # [(start_col, end_col), ...]
    
    # Supervisor routing decisions
    agents_to_run: list[str]          # Which agents the supervisor chose
    
    # Issues collected from each agent (use operator.add to merge lists)
    issues: Annotated[list[Issue], operator.add]
    
    # Agent tracking
    agent_statuses: Annotated[list[AgentStatus], operator.add]
    
    # Final report
    health_score: int
    executive_summary: str
    top_priorities: list[str]
    generated_at: str
