"""Account schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal


class AccountBase(BaseModel):
    """Base account schema"""
    name: str
    account_type: str


class AccountCreate(BaseModel):
    """Schema for linking a new account"""
    public_token: str


class AccountResponse(BaseModel):
    """Schema for account response"""
    id: UUID
    user_id: UUID
    plaid_account_id: str
    name: str
    official_name: Optional[str]
    account_type: str
    account_subtype: Optional[str]
    mask: Optional[str]
    current_balance: Decimal
    available_balance: Optional[Decimal]
    limit_amount: Optional[Decimal]
    currency: str
    institution_name: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]
    sync_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccountBalance(BaseModel):
    """Schema for account balance"""
    current: Decimal
    available: Optional[Decimal]
    limit: Optional[Decimal]
    currency: str


class LinkTokenResponse(BaseModel):
    """Schema for link token response"""
    link_token: str
    expiration: str
