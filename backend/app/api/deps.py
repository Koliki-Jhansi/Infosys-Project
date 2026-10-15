from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == uid).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def normalize_role(role: Any) -> str:
    if hasattr(role, "value"):
        return str(role.value).strip().upper()
    return str(role).strip().upper()

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = normalize_role(current_user.role)
        allowed_role_strs = [normalize_role(r) for r in allowed_roles]

        # Symmetrical aliasing: REQUESTER and PASSENGER represent identical customer clearance
        if "PASSENGER" in allowed_role_strs and user_role_str == "REQUESTER":
            user_role_str = "PASSENGER"
        elif "REQUESTER" in allowed_role_strs and user_role_str == "PASSENGER":
            user_role_str = "REQUESTER"

        if user_role_str not in allowed_role_strs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires one of roles: {[r.value if hasattr(r, 'value') else str(r) for r in allowed_roles]}",
            )
        return current_user
    return role_checker

get_admin_user = require_roles([UserRole.ADMIN])
get_support_or_admin = require_roles([UserRole.ADMIN, UserRole.SUPPORT_ENGINEER, UserRole.SUPPORT_AGENT])


