"""Agent memory system with vector store"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.agents import AgentMemory
from app.services.categorization import categorizer
import logging

logger = logging.getLogger(__name__)


class SharedMemory:
    """Shared memory system for agents"""
    
    def __init__(self, db: AsyncSession):
        """Initialize shared memory"""
        self.db = db
    
    async def add(
        self,
        agent_name: str,
        content: str,
        memory_type: str = "episodic",
        metadata: Optional[Dict[str, Any]] = None,
        importance: str = "medium",
        ttl_hours: Optional[int] = None,
    ) -> AgentMemory:
        """
        Add memory to shared store
        
        Args:
            agent_name: Name of the agent
            content: Memory content
            memory_type: Type (short_term, long_term, episodic, semantic)
            metadata: Additional metadata
            importance: Importance level (low, medium, high)
            ttl_hours: Time to live in hours
            
        Returns:
            Created memory
        """
        # Generate embedding
        embedding = categorizer.generate_embedding(content)
        
        # Calculate expiration
        expires_at = None
        if ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        memory = AgentMemory(
            agent_name=agent_name,
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            embedding=embedding,
            importance=importance,
            expires_at=expires_at,
        )
        
        self.db.add(memory)
        await self.db.flush()
        
        logger.info(f"Added {memory_type} memory for {agent_name}")
        return memory
    
    async def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[AgentMemory]:
        """
        Semantic search in memory
        
        Args:
            query: Search query
            agent_name: Filter by agent
            memory_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        # Generate query embedding
        query_embedding = categorizer.generate_embedding(query)
        
        # Build query
        stmt = select(AgentMemory).where(
            (AgentMemory.expires_at.is_(None)) | (AgentMemory.expires_at > datetime.utcnow())
        )
        
        if agent_name:
            stmt = stmt.where(AgentMemory.agent_name == agent_name)
        if memory_type:
            stmt = stmt.where(AgentMemory.memory_type == memory_type)
        
        # Order by similarity
        stmt = stmt.order_by(
            AgentMemory.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        memories = result.scalars().all()
        
        # Update accessed_at
        for memory in memories:
            memory.accessed_at = datetime.utcnow()
        
        await self.db.flush()
        
        return memories
    
    async def get_recent(
        self,
        agent_name: str,
        n: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[AgentMemory]:
        """
        Get recent memories
        
        Args:
            agent_name: Agent name
            n: Number of memories
            memory_type: Filter by type
            
        Returns:
            Recent memories
        """
        stmt = select(AgentMemory).where(
            AgentMemory.agent_name == agent_name,
            (AgentMemory.expires_at.is_(None)) | (AgentMemory.expires_at > datetime.utcnow())
        )
        
        if memory_type:
            stmt = stmt.where(AgentMemory.memory_type == memory_type)
        
        stmt = stmt.order_by(AgentMemory.created_at.desc()).limit(n)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_importance(
        self,
        agent_name: str,
        importance: str = "high",
        limit: int = 10,
    ) -> List[AgentMemory]:
        """Get memories by importance level"""
        stmt = select(AgentMemory).where(
            AgentMemory.agent_name == agent_name,
            AgentMemory.importance == importance,
            (AgentMemory.expires_at.is_(None)) | (AgentMemory.expires_at > datetime.utcnow())
        ).order_by(AgentMemory.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def clear_expired(self) -> int:
        """Clear expired memories"""
        stmt = delete(AgentMemory).where(
            AgentMemory.expires_at.isnot(None),
            AgentMemory.expires_at < datetime.utcnow()
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        count = result.rowcount
        logger.info(f"Cleared {count} expired memories")
        return count
    
    async def clear_agent_memories(
        self,
        agent_name: str,
        memory_type: Optional[str] = None,
    ) -> int:
        """Clear all memories for an agent"""
        stmt = delete(AgentMemory).where(AgentMemory.agent_name == agent_name)
        
        if memory_type:
            stmt = stmt.where(AgentMemory.memory_type == memory_type)
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        count = result.rowcount
        logger.info(f"Cleared {count} memories for {agent_name}")
        return count
