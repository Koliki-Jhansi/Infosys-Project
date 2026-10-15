from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.setting import AppSetting
from app.schemas.setting import SettingResponse, SettingUpdate
from app.api.deps import get_current_user, get_admin_user
from app.core.config import settings
from app.services.audit.audit_service import record_audit_event

router = APIRouter(prefix="/settings", tags=["Settings"])

DEFAULT_SETTINGS = {
    "CONFIDENCE_THRESHOLD": ("70.0", "Confidence threshold percentage required for automated routing without human review"),
    "AI_MOCK_MODE": ("true" if settings.AI_MOCK_MODE else "false", "Run AI classification and agents in deterministic mock mode"),
    "JIRA_MOCK_MODE": ("true" if settings.JIRA_MOCK_MODE else "false", "Run Jira integration in simulated mode"),
    "MAX_AGENT_REVISION_CYCLES": (str(settings.MAX_AGENT_REVISION_CYCLES), "Maximum allowed agent revision iterations"),
}

def ensure_default_settings(db: Session):
    for key, (val, desc) in DEFAULT_SETTINGS.items():
        existing = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not existing:
            setting_obj = AppSetting(key=key, value=val, description=desc)
            db.add(setting_obj)
    db.commit()

@router.get("", response_model=List[SettingResponse])
def get_all_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ensure_default_settings(db)
    return db.query(AppSetting).all()

@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    setting_in: SettingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    ensure_default_settings(db)
    setting_obj = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting_obj:
        setting_obj = AppSetting(key=key, value=setting_in.value, description=f"Custom setting {key}")
        db.add(setting_obj)
    else:
        old_val = setting_obj.value
        setting_obj.value = setting_in.value

    db.commit()
    db.refresh(setting_obj)

    record_audit_event(
        db=db,
        entity_type="SETTING",
        entity_id=key,
        action="SETTING_UPDATED",
        actor_id=current_user.id,
        details={"key": key, "new_value": setting_in.value}
    )

    return setting_obj
