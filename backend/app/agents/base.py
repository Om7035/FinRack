"""Base agent class with LangGraph integration"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agents import AgentTask
from app.agents.memory import SharedMemory
from app.agents.communication import agent_communication, AgentMessage
from app.services.llm_service import llm_service, LLMProvider
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentState(Dict[str, Any]):
    """Agent state for LangGraph"""
    pass


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(
        self,
        name: str,
        description: str,
        db: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            description: Agent description
            db: Database session
            llm_provider: Preferred LLM provider
        """
        self.name = name
        self.description = description
        self.db = db
        self.llm_provider = llm_provider
        self.memory = SharedMemory(db)
        self.tools: Dict[str, Callable] = {}
        
        # Subscribe to messages
        agent_communication.subscribe(self.name, self._handle_message)
        
        logger.info(f"Initialized agent: {self.name}")
    
    def register_tool(self, name: str, func: Callable, description: str) -> None:
        """
        Register a tool for the agent
        
        Args:
            name: Tool name
            func: Tool function
            description: Tool description
        """
        self.tools[name] = {
            'function': func,
            'description': description,
        }
        logger.info(f"Registered tool '{name}' for {self.name}")
    
    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute agent task
        
        Args:
            task_type: Type of task
            input_data: Input data
            user_id: User ID
            
        Returns:
            Task result
        """
        # Create task record
        task = AgentTask(
            user_id=user_id,
            agent_name=self.name,
            task_type=task_type,
            status="running",
            input_data=input_data,
        )
        self.db.add(task)
        await self.db.flush()
        
        task.started_at = datetime.utcnow()
        
        try:
            # Execute task
            result = await self._execute_task(task_type, input_data, user_id)
            
            # Update task
            task.status = "completed"
            task.output_data = result
            task.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Task completed: {self.name} - {task_type}")
            return result
            
        except Exception as e:
            logger.error(f"Task failed: {self.name} - {task_type}: {e}")
            
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            raise
    
    async def _execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute specific task (to be overridden by subclasses)
        
        Args:
            task_type: Type of task
            input_data: Input data
            user_id: User ID
            
        Returns:
            Task result
        """
        raise NotImplementedError("Subclasses must implement _execute_task")
    
    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Use LLM to think/reason
        
        Args:
            prompt: User prompt
            context: Additional context
            system_prompt: System prompt
            
        Returns:
            LLM response
        """
        # Build full prompt with context
        full_prompt = prompt
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"Context:\n{context_str}\n\nTask:\n{prompt}"
        
        # Generate response
        response = await llm_service.generate(
            prompt=full_prompt,
            provider=self.llm_provider,
            system_prompt=system_prompt or f"You are {self.name}, {self.description}",
            temperature=0.7,
            max_tokens=1000,
        )
        
        return response
    
    async def remember(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: str = "medium",
    ) -> None:
        """
        Store memory
        
        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance level
        """
        await self.memory.add(
            agent_name=self.name,
            content=content,
            memory_type=memory_type,
            importance=importance,
        )
    
    async def recall(
        self,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Recall relevant memories
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of memory contents
        """
        memories = await self.memory.search(
            query=query,
            agent_name=self.name,
            limit=limit,
        )
        
        return [mem.content for mem in memories]
    
    async def send_message(
        self,
        to_agent: str,
        message_type: str,
        content: Any,
    ) -> None:
        """
        Send message to another agent
        
        Args:
            to_agent: Recipient agent name
            message_type: Message type
            content: Message content
        """
        await agent_communication.send_message(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
        )
    
    async def broadcast(
        self,
        message_type: str,
        content: Any,
    ) -> None:
        """
        Broadcast message to all agents
        
        Args:
            message_type: Message type
            content: Message content
        """
        await agent_communication.broadcast(
            from_agent=self.name,
            message_type=message_type,
            content=content,
        )
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """
        Handle incoming message
        
        Args:
            message: Received message
        """
        logger.info(f"{self.name} received message from {message.from_agent}: {message.message_type}")
        
        # Store in memory
        await self.remember(
            content=f"Received {message.message_type} from {message.from_agent}: {message.content}",
            memory_type="episodic",
            importance="medium",
        )
    
    async def use_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        Use a registered tool
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments
            
        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        func = tool['function']
        
        logger.info(f"{self.name} using tool: {tool_name}")
        
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)


import asyncio
