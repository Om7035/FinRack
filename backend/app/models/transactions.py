"""Transaction models with vector embeddings for semantic search"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, Numeric, Date, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Transaction(Base):
    """Transaction model with vector embeddings for semantic search"""
    
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Plaid Integration
    plaid_transaction_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # Transaction Details
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    date = Column(Date, nullable=False, index=True)
    authorized_date = Column(Date, nullable=True)
    
    # Description
    name = Column(String(500), nullable=False)
    original_description = Column(Text, nullable=True)
    
    # Merchant Information
    merchant_name = Column(String(255), nullable=True, index=True)
    merchant_entity_id = Column(String(255), nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    category_detailed = Column(String(255), nullable=True)
    category_confidence = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Location
    location_address = Column(String(500), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    location_postal_code = Column(String(20), nullable=True)
    location_country = Column(String(2), nullable=True)
    location_lat = Column(Numeric(10, 7), nullable=True)
    location_lon = Column(Numeric(10, 7), nullable=True)
    
    # Payment Details
    payment_channel = Column(String(50), nullable=True)  # online, in store, other
    payment_method = Column(String(50), nullable=True)  # card, ach, etc.
    
    # Transaction Type
    transaction_type = Column(String(50), nullable=True)  # place, online, special, unresolved
    is_pending = Column(Boolean, default=False, nullable=False)
    
    # User Modifications
    user_category = Column(String(100), nullable=True)  # User-assigned category
    user_notes = Column(Text, nullable=True)
    is_hidden = Column(Boolean, default=False, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    
    # Receipt
    receipt_url = Column(Text, nullable=True)
    has_receipt = Column(Boolean, default=False, nullable=False)
    
    # Vector Embedding for Semantic Search (1536 dimensions for OpenAI embeddings)
    embedding = Column(Vector(1536), nullable=True)
    
    # Fraud Detection
    fraud_score = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    is_suspicious = Column(Boolean, default=False, nullable=False)
    fraud_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("BankAccount", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index("idx_transaction_date", "date"),
        Index("idx_transaction_category", "category"),
        Index("idx_transaction_amount", "amount"),
        Index("idx_transaction_merchant", "merchant_name"),
        Index("idx_transaction_account_date", "account_id", "date"),
        Index("idx_transaction_embedding", "embedding", postgresql_using="ivfflat"),  # Vector index
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, merchant={self.merchant_name})>"

    @property
    def final_category(self) -> str:
        """Get the final category (user-assigned or auto-assigned)"""
        return self.user_category or self.category or "Uncategorized"
