"""Transaction schemas"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal


class TransactionBase(BaseModel):
    """Base transaction schema"""
    amount: Decimal
    date: date
    name: str


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    id: UUID
    account_id: UUID
    plaid_transaction_id: Optional[str]
    amount: Decimal
    currency: str
    date: date
    authorized_date: Optional[date]
    name: str
    merchant_name: Optional[str]
    category: Optional[str]
    user_category: Optional[str]
    category_confidence: Optional[Decimal]
    payment_channel: Optional[str]
    is_pending: bool
    is_recurring: bool
    has_receipt: bool
    fraud_score: Optional[Decimal]
    is_suspicious: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionUpdate(BaseModel):
    """Schema for updating transaction"""
    user_category: Optional[str] = None
    user_notes: Optional[str] = None
    is_hidden: Optional[bool] = None


class TransactionFilter(BaseModel):
    """Schema for transaction filters"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    merchant_name: Optional[str] = None
    is_pending: Optional[bool] = None
    account_id: Optional[UUID] = None


class TransactionSearch(BaseModel):
    """Schema for semantic search"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class TransactionStats(BaseModel):
    """Schema for transaction statistics"""
    total_transactions: int
    total_spent: Decimal
    total_income: Decimal
    net_amount: Decimal
    by_category: dict
    by_month: dict
    average_transaction: Decimal


class BulkCategorize(BaseModel):
    """Schema for bulk categorization"""
    transaction_ids: List[UUID]
    category: str
