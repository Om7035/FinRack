"""Financial goal models"""
import uuid
from datetime import datetime, date
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, ForeignKey, Date, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class FinancialGoal(Base):
    """Financial goal model"""
    __tablename__ = "financial_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Goal details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # emergency_fund, vacation, house, car, retirement
    
    # Amounts
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Timeline
    deadline = Column(Date, nullable=True)
    
    # Priority
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high
    
    # Status
    status = Column(String(20), default="in_progress", nullable=False)  # in_progress, achieved, abandoned
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    achieved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")


class GoalProgress(Base):
    """Goal progress tracking model"""
    __tablename__ = "goal_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("financial_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress details
    amount = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamp
    date = Column(Date, default=date.today, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    goal = relationship("FinancialGoal", back_populates="progress_entries")
