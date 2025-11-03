"""Transaction schemas"""
from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    """Base transaction schema"""
    amount: Decimal
    date: date
    name: str
    category: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Transaction update schema"""
    category: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Transaction response schema"""
    id: str
    account_id: str
    amount: Decimal
    date: date
    authorized_date: Optional[date]
    name: str
    merchant_name: Optional[str]
    category: Optional[str]
    category_detailed: Optional[str]
    payment_channel: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionSearchRequest(BaseModel):
    """Semantic search request"""
    query: str
    limit: int = 20


class TransactionStats(BaseModel):
    """Transaction statistics"""
    total_transactions: int
    total_spent: Decimal
    total_income: Decimal
    by_category: dict[str, Decimal]
    by_month: dict[str, Decimal]
