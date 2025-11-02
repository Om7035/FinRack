"""Transaction models"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, String, Numeric, ForeignKey, Date, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Transaction(Base):
    """Transaction model with vector embeddings for semantic search"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plaid integration
    plaid_transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Transaction details
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    authorized_date = Column(Date, nullable=True)
    
    # Description
    name = Column(String(500), nullable=False)
    merchant_name = Column(String(255), nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    category_detailed = Column(String(255), nullable=True)
    
    # Location
    location_address = Column(String(500), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    location_postal_code = Column(String(20), nullable=True)
    location_country = Column(String(2), nullable=True)
    location_lat = Column(Numeric(10, 7), nullable=True)
    location_lon = Column(Numeric(10, 7), nullable=True)
    
    # Payment details
    payment_channel = Column(String(50), nullable=True)  # online, in store, other
    
    # User notes
    notes = Column(Text, nullable=True)
    
    # Vector embedding for semantic search (384 dimensions for sentence-transformers)
    embedding = Column(Vector(384), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("BankAccount", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('ix_transactions_date_amount', 'date', 'amount'),
        Index('ix_transactions_category_date', 'category', 'date'),
        Index('ix_transactions_embedding', 'embedding', postgresql_using='ivfflat'),
    )
