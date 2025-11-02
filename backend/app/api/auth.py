"""Authentication API endpoints"""

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.users import User, Profile
from app.schemas.auth import UserCreate, UserLogin, Token, TokenRefresh, MFASetup, MFAVerify
from app.schemas.users import UserResponse
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_mfa_secret,
    verify_mfa_token,
    get_mfa_provisioning_uri,
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **full_name**: Optional full name
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_superuser=False,
        is_verified=False,
        mfa_enabled=False,
    )
    
    db.add(new_user)
    await db.flush()
    
    # Create user profile
    profile = Profile(
        user_id=new_user.id,
        full_name=user_data.full_name,
    )
    
    db.add(profile)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login with email and password
    
    Returns access and refresh tokens
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Check MFA if enabled
    if user.mfa_enabled:
        # MFA token should be provided in the password field after a colon
        # Format: password:mfa_token
        parts = form_data.password.split(":")
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA token required"
            )
        
        password, mfa_token = parts
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not verify_mfa_token(user.mfa_secret, mfa_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token"
            )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Setup 2FA for current user
    
    Returns secret and QR code URI for authenticator app
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled"
        )
    
    # Generate new secret
    secret = generate_mfa_secret()
    qr_uri = get_mfa_provisioning_uri(secret, current_user.email)
    
    # Store secret (not enabled yet)
    current_user.mfa_secret = secret
    await db.commit()
    
    # Generate backup codes (simplified - in production, hash these)
    backup_codes = [generate_mfa_secret()[:8] for _ in range(10)]
    
    return {
        "secret": secret,
        "qr_code_uri": qr_uri,
        "backup_codes": backup_codes
    }


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify MFA token and enable 2FA
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled"
        )
    
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up. Call /mfa/setup first"
        )
    
    # Verify token
    if not verify_mfa_token(current_user.mfa_secret, mfa_data.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    await db.commit()
    
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    mfa_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Disable 2FA for current user
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled"
        )
    
    # Verify token before disabling
    if not verify_mfa_token(current_user.mfa_secret, mfa_data.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    await db.commit()
    
    return {"message": "MFA disabled successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user
    
    Note: In a production app, you would invalidate the token here
    by adding it to a blacklist in Redis
    """
    return {"message": "Logged out successfully"}
