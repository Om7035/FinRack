"""AI Agent models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class AgentTask(Base):
    """Agent task execution tracking"""
    __tablename__ = "agent_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Agent details
    agent_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    
    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    
    # Input/Output
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="agent_tasks")


class AgentMemory(Base):
    """Agent memory storage for context and learning"""
    __tablename__ = "agent_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Agent details
    agent_name = Column(String(100), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # short_term, long_term, episodic, semantic
    
    # Content
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384), nullable=True)
    
    # Importance score (0-1)
    importance = Column(String(20), default="medium", nullable=False)  # low, medium, high
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
