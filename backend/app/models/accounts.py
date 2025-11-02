"""Bank Account models"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class BankAccount(Base):
    """Bank account model linked to Plaid"""
    
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Plaid Integration
    plaid_account_id = Column(String(255), unique=True, index=True, nullable=False)
    plaid_access_token = Column(String(255), nullable=False)  # Encrypted in production
    plaid_item_id = Column(String(255), nullable=True)
    
    # Account Information
    name = Column(String(255), nullable=False)
    official_name = Column(String(255), nullable=True)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, investment
    account_subtype = Column(String(50), nullable=True)
    mask = Column(String(10), nullable=True)  # Last 4 digits
    
    # Balance Information
    current_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    available_balance = Column(Numeric(15, 2), nullable=True)
    limit_amount = Column(Numeric(15, 2), nullable=True)  # For credit cards
    currency = Column(String(3), default="USD", nullable=False)
    
    # Institution Information
    institution_id = Column(String(255), nullable=True)
    institution_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_manual = Column(Boolean, default=False, nullable=False)  # Manually added account
    
    # Sync Information
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="pending", nullable=False)  # pending, syncing, success, error
    sync_error = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_user_accounts", "user_id", "is_active"),
        Index("idx_plaid_account", "plaid_account_id"),
    )

    def __repr__(self):
        return f"<BankAccount(id={self.id}, name={self.name}, type={self.account_type})>"
