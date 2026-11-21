"""
deps.py - FastAPI Authentication and Role Authorization Dependencies

Provides reusable dependency injectors for endpoints to authenticate JWT tokens,
retrieve the active user from the database, and enforce Role-Based Access Control (RBAC).
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models import User

# OAuth2 scheme configured to use token endpoint for swagger authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the Bearer token, extracts user identity, and fetches user from DB.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Please login.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: Optional[str] = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account."
        )

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns User if valid token is provided, otherwise None.
    """
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if user and user.is_active:
        return user
    if payload.get("role"):
        return User(
            id=payload.get("user_id", 0),
            username=username,
            role=payload.get("role"),
            email=f"{username}@domain.edu",
            is_active=True
        )
    return None


def require_roles(allowed_roles: List[str]):
    """
    Factory dependency to enforce Role-Based Access Control (RBAC).
    Example: Depends(require_roles(["admin", "teacher"]))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role in {allowed_roles}, but current user has role '{current_user.role}'."
            )
        return current_user

    return role_checker
