"""Agent communication system"""
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message between agents"""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.message_type = message_type
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.id = f"{from_agent}_{to_agent}_{self.timestamp.timestamp()}"


class AgentCommunication:
    """Communication system for agent collaboration"""
    
    def __init__(self):
        """Initialize communication system"""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[AgentMessage] = []
        self.max_history = 1000
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        """
        Send message from one agent to another
        
        Args:
            from_agent: Sender agent name
            to_agent: Recipient agent name
            message_type: Type of message
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Created message
        """
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            metadata=metadata,
        )
        
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        # Notify subscribers
        await self._notify_subscribers(message)
        
        logger.info(f"Message sent: {from_agent} -> {to_agent} ({message_type})")
        return message
    
    async def broadcast(
        self,
        from_agent: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[AgentMessage]:
        """
        Broadcast message to all agents
        
        Args:
            from_agent: Sender agent name
            message_type: Type of message
            content: Message content
            metadata: Additional metadata
            
        Returns:
            List of created messages
        """
        messages = []
        
        # Send to all subscribers
        for agent_name in self.subscribers.keys():
            if agent_name != from_agent:
                message = await self.send_message(
                    from_agent=from_agent,
                    to_agent=agent_name,
                    message_type=message_type,
                    content=content,
                    metadata=metadata,
                )
                messages.append(message)
        
        logger.info(f"Broadcast from {from_agent}: {message_type} to {len(messages)} agents")
        return messages
    
    def subscribe(
        self,
        agent_name: str,
        callback: Callable[[AgentMessage], Any],
    ) -> None:
        """
        Subscribe agent to receive messages
        
        Args:
            agent_name: Agent name
            callback: Callback function to handle messages
        """
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        
        self.subscribers[agent_name].append(callback)
        logger.info(f"Agent {agent_name} subscribed to messages")
    
    def unsubscribe(self, agent_name: str) -> None:
        """Unsubscribe agent from messages"""
        if agent_name in self.subscribers:
            del self.subscribers[agent_name]
            logger.info(f"Agent {agent_name} unsubscribed")
    
    async def _notify_subscribers(self, message: AgentMessage) -> None:
        """Notify subscribers of new message"""
        if message.to_agent in self.subscribers:
            for callback in self.subscribers[message.to_agent]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
    
    def get_conversation(
        self,
        agent1: str,
        agent2: str,
        limit: int = 50,
    ) -> List[AgentMessage]:
        """
        Get conversation between two agents
        
        Args:
            agent1: First agent name
            agent2: Second agent name
            limit: Maximum messages
            
        Returns:
            List of messages
        """
        conversation = [
            msg for msg in self.message_history
            if (msg.from_agent == agent1 and msg.to_agent == agent2) or
               (msg.from_agent == agent2 and msg.to_agent == agent1)
        ]
        
        return conversation[-limit:]
    
    def get_agent_messages(
        self,
        agent_name: str,
        limit: int = 50,
    ) -> List[AgentMessage]:
        """Get all messages for an agent"""
        messages = [
            msg for msg in self.message_history
            if msg.from_agent == agent_name or msg.to_agent == agent_name
        ]
        
        return messages[-limit:]
    
    def clear_history(self) -> None:
        """Clear message history"""
        self.message_history.clear()
        logger.info("Message history cleared")


# Global instance
agent_communication = AgentCommunication()
