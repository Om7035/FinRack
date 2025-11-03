"""Goal schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal


class GoalCreate(BaseModel):
    """Goal creation schema"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=0, ge=0)
    deadline: Optional[date] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class GoalUpdate(BaseModel):
    """Goal update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[Decimal] = Field(None, gt=0)
    current_amount: Optional[Decimal] = Field(None, ge=0)
    deadline: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(in_progress|achieved|abandoned)$")


class GoalResponse(BaseModel):
    """Goal response schema"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[date]
    priority: str
    status: str
    is_active: bool
    created_at: datetime
    achieved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class GoalProgressAdd(BaseModel):
    """Add progress to goal"""
    amount: Decimal = Field(gt=0)
    notes: Optional[str] = None


class GoalProjection(BaseModel):
    """Goal projection schema"""
    goal: GoalResponse
    percentage_complete: float
    amount_remaining: Decimal
    days_until_deadline: Optional[int]
    required_monthly_savings: Optional[Decimal]
    projected_completion_date: Optional[date]
    probability_of_success: Optional[float]
    on_track: bool
