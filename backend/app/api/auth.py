"""Authentication API endpoints"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.users import User, Profile
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    UserWithProfile,
    TwoFactorSetup,
    TwoFactorVerify,
    PasswordChange,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code,
    verify_totp,
    validate_password_strength,
)
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Register a new user"""
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.flush()
    
    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=user_data.full_name,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Login and get access token"""
    # Get user
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
) -> dict:
    """Refresh access token"""
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
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserWithProfile)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get current user information"""
    # Load profile
    result = await db.execute(select(Profile).where(Profile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_2fa_enabled": current_user.is_2fa_enabled,
        "created_at": current_user.created_at,
        "full_name": profile.full_name if profile else None,
        "phone_number": profile.phone_number if profile else None,
        "timezone": profile.timezone if profile else "UTC",
        "currency": profile.currency if profile else "USD",
    }


@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Setup 2FA for user"""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    # Generate TOTP secret
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    qr_code = generate_qr_code(uri)
    
    # Generate backup codes (simplified - in production, hash these)
    import secrets
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    
    # Store secret (not enabled yet until verified)
    current_user.totp_secret = secret
    await db.commit()
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes
    }


@router.post("/2fa/verify")
async def verify_2fa(
    verify_data: TwoFactorVerify,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Verify and enable 2FA"""
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up. Call /2fa/setup first"
        )
    
    if not verify_totp(current_user.totp_secret, verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    # Enable 2FA
    current_user.is_2fa_enabled = True
    await db.commit()
    
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    verify_data: TwoFactorVerify,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Disable 2FA"""
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    if not verify_totp(current_user.totp_secret, verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    # Disable 2FA
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    await db.commit()
    
    return {"message": "2FA disabled successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Logout user (client should delete tokens)"""
    return {"message": "Logged out successfully"}
