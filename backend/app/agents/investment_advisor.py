"""Investment Advisor Agent - Portfolio analysis"""
from typing import Dict, Any
from app.agents.base import BaseAgent
import logging

logger = logging.getLogger(__name__)


class InvestmentAdvisorAgent(BaseAgent):
    """Agent for investment advice and portfolio analysis"""
    
    def __init__(self, db):
        super().__init__(
            name="investment_advisor",
            description="an AI investment advisor that analyzes portfolios and provides investment recommendations",
            db=db,
        )
    
    async def _execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute investment advisor task"""
        
        if task_type == "analyze_portfolio":
            return await self._analyze_portfolio(user_id, input_data)
        elif task_type == "suggest_allocation":
            return await self._suggest_allocation(user_id, input_data)
        else:
            return await self._general_investment_query(user_id, input_data)
    
    async def _analyze_portfolio(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze investment portfolio"""
        portfolio = input_data.get('portfolio', {})
        
        # Generate analysis using LLM
        analysis = await self.think(
            prompt="Analyze this investment portfolio and provide recommendations for diversification and risk management.",
            context={"portfolio": portfolio},
        )
        
        return {
            "analysis": analysis,
            "portfolio_summary": portfolio,
        }
    
    async def _suggest_allocation(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Suggest asset allocation"""
        risk_profile = input_data.get('risk_profile', 'moderate')
        
        # Standard allocations by risk profile
        allocations = {
            "conservative": {"stocks": 40, "bonds": 50, "cash": 10},
            "moderate": {"stocks": 60, "bonds": 30, "cash": 10},
            "aggressive": {"stocks": 80, "bonds": 15, "cash": 5},
        }
        
        suggested = allocations.get(risk_profile, allocations["moderate"])
        
        # Get LLM recommendations
        recommendations = await self.think(
            prompt=f"Explain this asset allocation strategy for a {risk_profile} investor and provide additional insights.",
            context={"allocation": suggested, "risk_profile": risk_profile},
        )
        
        return {
            "suggested_allocation": suggested,
            "risk_profile": risk_profile,
            "recommendations": recommendations,
        }
    
    async def _general_investment_query(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle general investment queries"""
        query = input_data.get('query', '')
        
        # Recall relevant memories
        memories = await self.recall(query, limit=3)
        
        response = await self.think(
            prompt=f"Answer this investment question: {query}",
            context={"memories": memories},
        )
        
        return {"response": response}
