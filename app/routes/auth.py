"""
auth.py - Authentication & Authorization REST API Endpoints

Provides:
- User registration with role allocation ('admin', 'teacher', 'student')
- Login via JSON payload or OAuth2 standard form data
- Signed JWT access token generation
- Identity inspection (/me) with RBAC validation
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import User
from app.schemas import UserCreate, UserResponse, UserLogin, Token
from app.core.security import create_access_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.deps import get_current_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new system user"
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with hashed password.
    Roles: 'admin', 'teacher', 'student'.
    """
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' is already taken."
        )

    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user_in.email}' is already registered."
        )

    return crud.create_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Login with JSON credentials to receive a JWT access token"
)
def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user with JSON body (username/email and password).
    Returns a cryptographically signed JWT access token.
    """
    user = crud.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    student_id = user.student_profile.student_id if user.student_profile else None

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "student_id": student_id
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        user_id=user.id,
        student_id=student_id
    )


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2 compatible token endpoint for Swagger docs authorization"
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Standard OAuth2 password flow endpoint consumed by Swagger UI 'Authorize' dialog.
    """
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    student_id = user.student_profile.student_id if user.student_profile else None
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "student_id": student_id
        }
    )

    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        user_id=user.id,
        student_id=student_id
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the profile and role of the currently authenticated JWT bearer.
    """
    return current_user
