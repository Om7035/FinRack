"""Authentication schemas"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithProfile(UserResponse):
    """User with profile response schema"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: str
    currency: str


class TwoFactorSetup(BaseModel):
    """2FA setup response schema"""
    secret: str
    qr_code: str
    backup_codes: list[str]


class TwoFactorVerify(BaseModel):
    """2FA verification schema"""
    token: str


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    """Password reset schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8)
