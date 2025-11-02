"""Financial Goal models"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, Date, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class FinancialGoal(Base):
    """Financial goal model for tracking savings and investment goals"""
    
    __tablename__ = "financial_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Goal Details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # emergency_fund, vacation, house, car, retirement, etc.
    
    # Financial Details
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Timeline
    deadline = Column(Date, nullable=True)
    start_date = Column(Date, default=date.today, nullable=False)
    
    # Priority
    priority = Column(String(20), default="medium", nullable=False)  # high, medium, low
    
    # Progress Tracking
    percentage_complete = Column(Numeric(5, 2), default=0.00, nullable=False)
    required_monthly_savings = Column(Numeric(15, 2), nullable=True)
    projected_completion_date = Column(Date, nullable=True)
    probability_of_success = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, achieved, abandoned, on_hold
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Linked Account (optional)
    linked_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True)
    
    # Milestones (JSON could be used, but we'll use a separate table for better querying)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    achieved_at = Column(DateTime, nullable=True)
    last_calculated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan", order_by="GoalProgress.date.desc()")

    # Indexes
    __table_args__ = (
        Index("idx_goal_user_status", "user_id", "status"),
        Index("idx_goal_deadline", "deadline"),
    )

    def __repr__(self):
        return f"<FinancialGoal(id={self.id}, name={self.name}, target={self.target_amount})>"

    @property
    def remaining_amount(self) -> float:
        """Calculate remaining amount to reach goal"""
        return float(self.target_amount - self.current_amount)

    @property
    def is_achieved(self) -> bool:
        """Check if goal is achieved"""
        return self.current_amount >= self.target_amount


class GoalProgress(Base):
    """Goal progress tracking model"""
    
    __tablename__ = "goal_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("financial_goals.id", ondelete="CASCADE"), nullable=False)
    
    # Progress Details
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(String(500), nullable=True)
    date = Column(Date, default=date.today, nullable=False)
    
    # Type
    entry_type = Column(String(50), default="contribution", nullable=False)  # contribution, withdrawal, adjustment
    
    # Source
    source = Column(String(100), nullable=True)  # manual, automatic, linked_account
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    goal = relationship("FinancialGoal", back_populates="progress_entries")

    # Indexes
    __table_args__ = (
        Index("idx_progress_goal_date", "goal_id", "date"),
    )

    def __repr__(self):
        return f"<GoalProgress(id={self.id}, goal_id={self.goal_id}, amount={self.amount})>"
