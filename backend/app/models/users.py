"""User models"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 2FA
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    
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


class Profile(Base):
    """User profile model"""
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Preferences stored as JSON
    preferences = Column(JSON, default={}, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")
