"""User schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProfileBase(BaseModel):
    """Base profile schema"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: str = "UTC"
    currency: str = "USD"
    language: str = "en"
    theme: str = "system"


class ProfileUpdate(BaseModel):
    """Schema for profile update"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    preferred_llm_provider: Optional[str] = None
    large_transaction_threshold: Optional[str] = None
    budget_warning_percentage: Optional[str] = None


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    id: UUID
    user_id: UUID
    full_name: Optional[str]
    phone_number: Optional[str]
    timezone: str
    currency: str
    date_format: str
    language: str
    theme: str
    preferred_llm_provider: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
