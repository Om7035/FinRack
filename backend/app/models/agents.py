"""AI Agent models for task tracking and memory"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, String, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class AgentTask(Base):
    """Agent task model for tracking AI agent executions"""
    
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Agent Details
    agent_name = Column(String(100), nullable=False, index=True)  # budget_guardian, fraud_sentinel, etc.
    task_type = Column(String(100), nullable=False)  # analyze, predict, recommend, alert, etc.
    
    # Task Details
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Execution Details
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Performance Metrics
    execution_time_ms = Column(String(20), nullable=True)
    tokens_used = Column(String(20), nullable=True)
    cost = Column(String(20), nullable=True)
    
    # LLM Details
    llm_provider = Column(String(50), nullable=True)  # ollama, groq, claude
    llm_model = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="agent_tasks")

    # Indexes
    __table_args__ = (
        Index("idx_agent_task_user_agent", "user_id", "agent_name"),
        Index("idx_agent_task_status", "status", "created_at"),
    )

    def __repr__(self):
        return f"<AgentTask(id={self.id}, agent={self.agent_name}, status={self.status})>"


class AgentMemory(Base):
    """Agent memory model for storing agent state and context"""
    
    __tablename__ = "agent_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Agent Details
    agent_name = Column(String(100), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # conversation, decision, preference, context
    
    # Memory Content
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Vector Embedding for Semantic Search
    embedding = Column(Vector(1536), nullable=True)
    
    # Scope
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Null for global memory
    session_id = Column(String(255), nullable=True)
    
    # Importance and Relevance
    importance_score = Column(String(10), nullable=True)  # 0.00 to 1.00
    access_count = Column(String(20), default="0", nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_memory_agent_type", "agent_name", "memory_type"),
        Index("idx_memory_user", "user_id", "created_at"),
        Index("idx_memory_embedding", "embedding", postgresql_using="ivfflat"),
    )

    def __repr__(self):
        return f"<AgentMemory(id={self.id}, agent={self.agent_name}, type={self.memory_type})>"
