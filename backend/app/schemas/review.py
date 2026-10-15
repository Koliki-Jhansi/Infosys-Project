from typing import Optional
from pydantic import BaseModel
import enum

class ReviewActionEnum(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OVERRIDE = "OVERRIDE"

class ReviewActionRequest(BaseModel):
    action: ReviewActionEnum
    notes: Optional[str] = None
    override_category: Optional[str] = None
    override_priority: Optional[str] = None

class ReviewResponse(BaseModel):
    success: bool
    ticket_id: int
    new_status: str
    message: str
