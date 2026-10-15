from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.ticket import TicketResponse

class PriorityStat(BaseModel):
    name: str
    count: int

class CategoryStat(BaseModel):
    name: str
    count: int

class StatusStat(BaseModel):
    name: str
    count: int

class VolumeTrendPoint(BaseModel):
    date: str
    count: int

class DashboardStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Core requested metrics
    total_tickets: int
    open_tickets: int = 0
    ai_resolved_tickets: int = 0
    escalated_tickets: int = 0
    avg_resolution_time: str = "18 mins"
    ai_resolution_rate: float = 0.0

    # Retained backward-compatible metrics
    critical_tickets: int = 0
    awaiting_review_tickets: int = 0
    eligible_for_automation_tickets: int = 0
    resolved_tickets: int = 0
    
    # Visual breakdowns
    priority_distribution: List[PriorityStat] = []
    category_distribution: List[CategoryStat] = []
    status_distribution: List[StatusStat] = []
    volume_trend: List[VolumeTrendPoint] = []
    recent_activity: List[TicketResponse] = []
