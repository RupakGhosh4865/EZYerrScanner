from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class SeverityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueModel(BaseModel):
    id: str
    agent: str
    title: str
    description: str
    severity: SeverityEnum
    affected_rows: List[int]
    affected_columns: List[str]
    suggested_fix: str
    count: int
    confidence: float = Field(..., ge=0.0, le=1.0)

class AgentStatusModel(BaseModel):
    name: str
    status: str
    duration_ms: int
    issue_count: int

class AnalysisRequest(BaseModel):
    # Just used for docs, as file upload uses Form/File
    pass

class AnalysisReport(BaseModel):
    metadata: Dict[str, Any]
    health_score: int
    issues: List[IssueModel]
    agent_statuses: List[AgentStatusModel]
    executive_summary: str
    top_priorities: List[str]
    generated_at: str
    domain: str
    total_issues_by_severity: Dict[str, int]
