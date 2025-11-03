"""Account schemas"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AccountBase(BaseModel):
    """Base account schema"""
    name: str
    account_type: str


class AccountCreate(BaseModel):
    """Account creation schema"""
    public_token: str


class AccountResponse(BaseModel):
    """Account response schema"""
    id: str
    user_id: str
    name: str
    official_name: Optional[str]
    account_type: str
    account_subtype: Optional[str]
    current_balance: float
    available_balance: float
    currency: str
    mask: Optional[str]
    is_active: bool
    last_synced: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LinkTokenResponse(BaseModel):
    """Link token response schema"""
    link_token: str
    expiration: str
