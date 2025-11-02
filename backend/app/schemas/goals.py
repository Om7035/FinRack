"""Financial goal schemas"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal


class GoalBase(BaseModel):
    """Base goal schema"""
    name: str = Field(..., min_length=1, max_length=255)
    target_amount: Decimal = Field(..., gt=0)
    category: str


class GoalCreate(GoalBase):
    """Schema for creating goal"""
    description: Optional[str] = None
    deadline: Optional[date] = None
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    current_amount: Decimal = Field(default=0, ge=0)


class GoalUpdate(BaseModel):
    """Schema for updating goal"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: Optional[Decimal] = Field(None, gt=0)
    deadline: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(active|achieved|abandoned|on_hold)$")


class GoalResponse(BaseModel):
    """Schema for goal response"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    category: str
    target_amount: Decimal
    current_amount: Decimal
    currency: str
    deadline: Optional[date]
    priority: str
    percentage_complete: Decimal
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GoalProgressCreate(BaseModel):
    """Schema for adding goal progress"""
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    entry_type: str = Field(default="contribution", pattern="^(contribution|withdrawal|adjustment)$")


class GoalProgressResponse(BaseModel):
    """Schema for goal progress response"""
    id: UUID
    goal_id: UUID
    amount: Decimal
    description: Optional[str]
    date: date
    entry_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class GoalProjection(BaseModel):
    """Schema for goal projections"""
    goal_id: UUID
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    percentage_complete: Decimal
    deadline: Optional[date]
    days_remaining: Optional[int]
    required_monthly_savings: Optional[Decimal]
    projected_completion_date: Optional[date]
    probability_of_success: Optional[Decimal]
    on_track: bool
