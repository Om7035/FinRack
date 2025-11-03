"""Budget schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal


class BudgetCreate(BaseModel):
    """Budget creation schema"""
    name: str
    category: str
    amount: Decimal = Field(gt=0)
    period: str = Field(pattern="^(weekly|monthly|yearly)$")
    start_date: date
    end_date: Optional[date] = None
    alert_threshold: int = Field(default=80, ge=0, le=100)


class BudgetUpdate(BaseModel):
    """Budget update schema"""
    name: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    alert_threshold: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    """Budget response schema"""
    id: str
    user_id: str
    name: str
    category: str
    amount: Decimal
    period: str
    start_date: date
    end_date: Optional[date]
    alert_threshold: int
    alert_enabled: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class BudgetProgress(BaseModel):
    """Budget progress schema"""
    budget: BudgetResponse
    spent: Decimal
    remaining: Decimal
    percentage_used: float
    is_exceeded: bool
    days_remaining: Optional[int]
