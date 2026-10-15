from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

class SettingUpdate(BaseModel):
    value: str
