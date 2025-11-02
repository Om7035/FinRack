"""Budget models"""
import uuid
from datetime import datetime, date
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Budget(Base):
    """Budget model"""
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Budget details
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Period
    period = Column(String(20), nullable=False)  # weekly, monthly, yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Alert settings
    alert_threshold = Column(Integer, default=80, nullable=False)  # Percentage (0-100)
    alert_enabled = Column(Boolean, default=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    alerts = relationship("BudgetAlert", back_populates="budget", cascade="all, delete-orphan")


class BudgetAlert(Base):
    """Budget alert model"""
    __tablename__ = "budget_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # threshold, exceeded, warning
    message = Column(String(500), nullable=False)
    threshold_percentage = Column(Integer, nullable=False)
    
    # Status
    is_triggered = Column(Boolean, default=False, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    budget = relationship("Budget", back_populates="alerts")
