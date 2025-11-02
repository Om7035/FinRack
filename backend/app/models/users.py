"""User and Profile models"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 2FA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    accounts = relationship("BankAccount", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Profile(Base):
    """User profile with additional information"""
    
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Personal Information
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    
    # Preferences
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    date_format = Column(String(20), default="MM/DD/YYYY", nullable=False)
    number_format = Column(String(20), default="1,000.00", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    theme = Column(String(20), default="system", nullable=False)  # light, dark, system
    
    # LLM Preferences
    preferred_llm_provider = Column(String(50), default="ollama", nullable=False)  # ollama, groq, claude
    
    # Notification Preferences (JSON)
    notification_preferences = Column(JSON, default={
        "email": {
            "transaction_alerts": True,
            "budget_alerts": True,
            "goal_milestones": True,
            "weekly_summary": True,
            "monthly_report": True
        },
        "sms": {
            "fraud_alerts": True,
            "large_transactions": True,
            "budget_exceeded": True
        },
        "push": {
            "all": True
        }
    })
    
    # Alert Thresholds
    large_transaction_threshold = Column(String(20), default="500.00", nullable=False)
    budget_warning_percentage = Column(String(10), default="80", nullable=False)
    
    # Additional Settings (JSON)
    settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id}, full_name={self.full_name})>"
