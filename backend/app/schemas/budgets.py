"""Budget schemas"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal


class BudgetBase(BaseModel):
    """Base budget schema"""
    name: str
    category: str
    amount: Decimal = Field(..., gt=0)
    period: str = Field(..., pattern="^(weekly|monthly|yearly|custom)$")


class BudgetCreate(BudgetBase):
    """Schema for creating budget"""
    start_date: date
    end_date: Optional[date] = None
    alert_threshold: Decimal = Field(default=80.0, ge=0, le=100)


class BudgetUpdate(BaseModel):
    """Schema for updating budget"""
    name: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    alert_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    """Schema for budget response"""
    id: UUID
    user_id: UUID
    name: str
    category: str
    amount: Decimal
    currency: str
    period: str
    start_date: date
    end_date: Optional[date]
    current_spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
    is_active: bool
    alert_threshold: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BudgetProgress(BaseModel):
    """Schema for budget progress"""
    budget_id: UUID
    budget_name: str
    category: str
    amount: Decimal
    current_spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
    is_exceeded: bool
    is_warning: bool
    days_remaining: int
    transactions_count: int
