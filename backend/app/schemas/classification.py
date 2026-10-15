from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class ClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    predicted_category: str
    priority: str
    criticality: str
    confidence_score: float
    explanation: str
    detected_keywords: List[str]
    potential_business_impact: str
    recommended_next_action: str
    missing_information: List[str]
    requires_human_review: bool
    review_reason: Optional[str] = None
    is_reviewed: bool
    reviewed_by_id: Optional[int] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    model_name: str
    confidence_breakdown: Optional[Dict[str, Any]] = None
    created_at: datetime
