"""Budget and Budget Alert models"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Budget(Base):
    """Budget model for tracking spending limits"""
    
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Budget Details
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Period
    period = Column(String(20), nullable=False)  # weekly, monthly, yearly, custom
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Current Status
    current_spent = Column(Numeric(15, 2), default=0.00, nullable=False)
    remaining = Column(Numeric(15, 2), nullable=False)
    percentage_used = Column(Numeric(5, 2), default=0.00, nullable=False)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    rollover_unused = Column(Boolean, default=False, nullable=False)
    alert_enabled = Column(Boolean, default=True, nullable=False)
    alert_threshold = Column(Numeric(5, 2), default=80.00, nullable=False)  # Percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_calculated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    alerts = relationship("BudgetAlert", back_populates="budget", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_budget_user_category", "user_id", "category"),
        Index("idx_budget_period", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<Budget(id={self.id}, category={self.category}, amount={self.amount})>"

    @property
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded"""
        return self.current_spent > self.amount

    @property
    def is_warning(self) -> bool:
        """Check if budget is in warning zone"""
        return self.percentage_used >= self.alert_threshold


class BudgetAlert(Base):
    """Budget alert model for notifications"""
    
    __tablename__ = "budget_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    
    # Alert Details
    alert_type = Column(String(50), nullable=False)  # warning, exceeded, approaching
    threshold = Column(Numeric(5, 2), nullable=False)  # Percentage that triggered alert
    message = Column(String(500), nullable=False)
    
    # Status
    is_triggered = Column(Boolean, default=False, nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    triggered_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    budget = relationship("Budget", back_populates="alerts")

    # Indexes
    __table_args__ = (
        Index("idx_alert_budget", "budget_id", "is_triggered"),
    )

    def __repr__(self):
        return f"<BudgetAlert(id={self.id}, type={self.alert_type}, triggered={self.is_triggered})>"
