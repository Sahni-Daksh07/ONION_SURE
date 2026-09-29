"""
Authentication Router
Smart India Hackathon 2026 - Problem Statement PS26031

Endpoints:
- POST /register : Register new user (inspector, officer, admin)
- POST /login    : Authenticate and issue JWT access/refresh tokens
- POST /refresh  : Refresh expired access token
- GET  /me       : Current authenticated user profile
"""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...config import settings
from ...models.entities import User, Role, UserRole
from ...schemas.api_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
)
from ...security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from ...services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user in the system and assigns specified roles."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Create user
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        phone=user_in.phone,
        procurement_centre_id=user_in.procurement_centre_id,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # Assign roles
    for role_name in user_in.role_names:
        role = db.query(Role).filter(Role.name == role_name.upper()).first()
        if not role:
            role = Role(name=role_name.upper(), description=f"Role {role_name.upper()}")
            db.add(role)
            db.flush()

        user_role = UserRole(user_id=new_user.id, role_id=role.id)
        db.add(user_role)

    # Audit registration
    AuditService.log_event(
        db=db,
        action="USER_REGISTERED",
        entity_type="User",
        entity_id=new_user.id,
        actor_id=new_user.id,
        new_values={"email": new_user.email, "roles": user_in.role_names},
    )

    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials and returns JWT access and refresh tokens."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    roles = [r.name for r in user.roles]
    access_token = create_access_token(subject=user.id, roles=roles)
    refresh_token = create_refresh_token(subject=user.id)

    # Audit login
    AuditService.log_event(
        db=db,
        action="USER_LOGIN",
        entity_type="User",
        entity_id=user.id,
        actor_id=user.id,
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(token_in: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issues a new access token using a valid refresh token."""
    payload = decode_token(token_in.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or exists",
        )

    roles = [r.name for r in user.roles]
    new_access_token = create_access_token(subject=user.id, roles=roles)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the profile of currently authenticated user."""
    return current_user
