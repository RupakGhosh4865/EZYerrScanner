from typing import TypedDict, Annotated, Any
import operator

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
    confidence: float    # 0.0 - 1.0

class ProposedAction(TypedDict):
    action_id: str           # uuid
    action_type: str         # "flag_cell" | "add_comment" | "update_status" |
                             # "create_audit_sheet" | "update_cell_value"
    target_row_id: int       # Smartsheet row ID (0 if sheet-level action)
    target_column_id: int    # Smartsheet column ID (0 if row-level)
    column_title: str        # Human-readable column name
    current_value: str       # What is there now
    proposed_value: str      # What the agent wants to set
    reason: str              # Plain English reason
    severity: str            # "HIGH" | "MEDIUM" | "LOW"
    agent: str               # Which agent proposed this
    risk_level: str          # "SAFE" | "REVIEW" | "DESTRUCTIVE"

class ExecutedAction(TypedDict):
    action_id: str
    action_type: str
    status: str              # "success" | "failed" | "skipped"
    smartsheet_response: str # API response summary
    executed_at: str

class GraphState(TypedDict):
    # === Smartsheet connection ===
    smartsheet_token: str        # API token (from env, never in logs)
    sheet_id: str                # Which sheet to audit
    sheet_name: str
    use_mock_server: bool        # True = WireMock, False = real Smartsheet API
    mock_test_name_prefix: str   # e.g. "smartagent-" for custom mappings

    # === Data ===
    dataframe: Any               # list[dict] serialized from DataFrame
    metadata: dict
    raw_rows: list[dict]         # Original Smartsheet rows with __row_id__
    column_map: dict             # {column_title: column_id}

    # === Schema intelligence ===
    domain: str
    column_types: dict
    primary_key_cols: list[str]
    date_col_pairs: list[tuple]

    # === Supervisor routing ===
    agents_to_run: list[str]

    # === Issues (annotated for parallel merge) ===
    issues: Annotated[list[Issue], operator.add]
    agent_statuses: Annotated[list[AgentStatus], operator.add]

    # === Action lifecycle ===
    proposed_actions: Annotated[list[ProposedAction], operator.add]
    approved_action_ids: list[str]            # Set by HITL step
    executed_actions: list[ExecutedAction]    # What actually ran
    audit_sheet_url: str                      # URL of created audit sheet

    # === Report ===
    rows_scanned: int
    health_score: int
    executive_summary: str
    top_priorities: list[str]
    generated_at: str
