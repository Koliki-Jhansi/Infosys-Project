from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class JiraStatusResponse(BaseModel):
    connected: bool
    mode: str  # "REAL_CLOUD" | "SIMULATED"
    project_key: str
    base_url: str
    default_issue_type: str
    configured_email: Optional[str] = None
    is_enabled: bool = True

class JiraTestConnectionResponse(BaseModel):
    success: bool
    mode: str
    message: str
    user: Optional[str] = None
    email: Optional[str] = None
    project_key: Optional[str] = None
    project_count: Optional[int] = None
    error: Optional[str] = None

class JiraProjectItem(BaseModel):
    id: str
    key: str
    name: str
    project_type_key: Optional[str] = "software"
    lead_name: Optional[str] = None
    avatar_url: Optional[str] = None

class JiraCommentItem(BaseModel):
    id: str
    author: str
    body: str
    created_at: str

class JiraTransitionItem(BaseModel):
    id: str
    name: str
    to_status: str

class JiraIssueItem(BaseModel):
    id: str
    key: str
    url: str
    project_key: str
    summary: str
    description: str
    issue_type: str
    priority: str
    status: str
    assignee_name: Optional[str] = None
    reporter_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    comments: List[JiraCommentItem] = Field(default_factory=list)
    transitions: List[JiraTransitionItem] = Field(default_factory=list)
    idempotency_key: Optional[str] = None

class JiraIssueListResponse(BaseModel):
    items: List[JiraIssueItem]
    total: int
    page: int
    size: int
    pages: int
    project_key: Optional[str] = None

class JiraCreateIssueRequest(BaseModel):
    project_key: Optional[str] = None
    summary: str
    description: str
    priority: str = "Medium"
    issue_type: Optional[str] = "Task"
    assignee: Optional[str] = None
    idempotency_key: Optional[str] = None

class JiraUpdateIssueRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None

class JiraTransitionRequest(BaseModel):
    transition_id: str
    comment: Optional[str] = None

class JiraAddCommentRequest(BaseModel):
    comment: str

class JiraIssueRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    workflow_id: Optional[int] = None
    jira_key: str
    jira_url: str
    project_key: str
    issue_type: str
    summary: str
    priority: str
    status: str
    idempotency_key: str
    created_at: datetime
