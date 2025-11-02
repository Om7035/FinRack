"""Bank account models"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class BankAccount(Base):
    """Bank account model"""
    __tablename__ = "bank_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plaid integration
    plaid_account_id = Column(String(255), unique=True, nullable=False, index=True)
    plaid_access_token = Column(String(255), nullable=False)
    plaid_item_id = Column(String(255), nullable=False)
    
    # Account details
    name = Column(String(255), nullable=False)
    official_name = Column(String(255), nullable=True)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, investment
    account_subtype = Column(String(50), nullable=True)
    
    # Balance
    current_balance = Column(Numeric(15, 2), default=0, nullable=False)
    available_balance = Column(Numeric(15, 2), default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Mask (last 4 digits)
    mask = Column(String(4), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
