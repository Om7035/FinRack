"""Finance Concierge Agent - Natural language interface"""
from typing import Dict, Any
from app.agents.base import BaseAgent
import logging

logger = logging.getLogger(__name__)


class FinanceConciergeAgent(BaseAgent):
    """Agent for natural language financial queries"""
    
    def __init__(self, db):
        super().__init__(
            name="finance_concierge",
            description="a friendly AI financial assistant that helps users understand their finances and answers questions",
            db=db,
        )
    
    async def _execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute concierge task"""
        
        query = input_data.get('query', '')
        context = input_data.get('context', {})
        
        # Recall relevant memories
        memories = await self.recall(query, limit=5)
        
        # Build context
        full_context = {
            "user_query": query,
            "memories": memories,
            **context,
        }
        
        # Generate response
        response = await self.think(
            prompt=f"""User question: {query}

Provide a helpful, friendly response. If you need specific data, explain what information would be helpful.""",
            context=full_context,
        )
        
        # Remember interaction
        await self.remember(
            content=f"User asked: {query}. Responded: {response[:200]}",
            memory_type="episodic",
            importance="medium",
        )
        
        # Check if should delegate to specialized agent
        delegation = await self._check_delegation(query)
        
        return {
            "response": response,
            "delegation_suggestion": delegation,
            "memories_used": len(memories),
        }
    
    async def _check_delegation(self, query: str) -> Dict[str, Any]:
        """Check if query should be delegated to specialized agent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['budget', 'spending', 'expense']):
            return {"should_delegate": True, "agent": "budget_guardian"}
        elif any(word in query_lower for word in ['fraud', 'suspicious', 'security']):
            return {"should_delegate": True, "agent": "fraud_sentinel"}
        elif any(word in query_lower for word in ['invest', 'portfolio', 'stock']):
            return {"should_delegate": True, "agent": "investment_advisor"}
        elif any(word in query_lower for word in ['goal', 'save', 'target']):
            return {"should_delegate": True, "agent": "wealth_planner"}
        
        return {"should_delegate": False, "agent": None}
