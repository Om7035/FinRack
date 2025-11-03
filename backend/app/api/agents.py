"""AI Agents API endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.users import User
from app.core.deps import get_current_active_user
from app.agents.orchestrator import AgentOrchestrator
from app.agents.budget_guardian import BudgetGuardianAgent
from app.agents.fraud_sentinel import FraudSentinelAgent
from app.agents.finance_concierge import FinanceConciergeAgent
from app.agents.investment_advisor import InvestmentAdvisorAgent

router = APIRouter(prefix="/api/agents", tags=["AI Agents"])


class AgentQuery(BaseModel):
    """Agent query request"""
    query: str
    agent: Optional[str] = None  # Specific agent or auto-route


class AgentResponse(BaseModel):
    """Agent response"""
    agent: str
    intent: Optional[str] = None
    response: dict


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    query_data: AgentQuery,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Query AI agents with natural language
    
    If agent is specified, routes to that agent.
    Otherwise, automatically routes based on intent classification.
    """
    try:
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(db)
        
        # Register agents
        orchestrator.register_agent(BudgetGuardianAgent(db))
        orchestrator.register_agent(FraudSentinelAgent(db))
        orchestrator.register_agent(FinanceConciergeAgent(db))
        orchestrator.register_agent(InvestmentAdvisorAgent(db))
        
        # Route query
        if query_data.agent:
            # Direct to specific agent
            if query_data.agent in orchestrator.agents:
                agent = orchestrator.agents[query_data.agent]
                result = await agent.execute(
                    task_type="general_query",
                    input_data={"query": query_data.query},
                    user_id=str(current_user.id),
                )
                return {
                    "agent": query_data.agent,
                    "response": result,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent '{query_data.agent}' not found"
                )
        else:
            # Auto-route based on intent
            result = await orchestrator.route_task(
                user_input=query_data.query,
                user_id=str(current_user.id),
            )
            
            return {
                "agent": result['agent'],
                "intent": result['intent'],
                "response": result['result'],
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent query failed: {str(e)}"
        )


@router.get("/budget/analyze")
async def analyze_budget(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Analyze budget and spending patterns"""
    agent = BudgetGuardianAgent(db)
    
    result = await agent.execute(
        task_type="analyze_spending",
        input_data={},
        user_id=str(current_user.id),
    )
    
    return result


@router.get("/budget/check")
async def check_budgets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Check all budgets for alerts"""
    agent = BudgetGuardianAgent(db)
    
    result = await agent.execute(
        task_type="check_budgets",
        input_data={},
        user_id=str(current_user.id),
    )
    
    return result


@router.get("/fraud/scan")
async def scan_fraud(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Scan recent transactions for fraud"""
    agent = FraudSentinelAgent(db)
    
    result = await agent.execute(
        task_type="scan_recent",
        input_data={},
        user_id=str(current_user.id),
    )
    
    return result


@router.get("/fraud/risk-score")
async def get_risk_score(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get account risk score"""
    agent = FraudSentinelAgent(db)
    
    result = await agent.execute(
        task_type="get_risk_score",
        input_data={},
        user_id=str(current_user.id),
    )
    
    return result


@router.get("/list")
async def list_agents() -> dict:
    """List available AI agents"""
    return {
        "agents": [
            {
                "name": "budget_guardian",
                "description": "Monitors budgets and analyzes spending patterns",
                "capabilities": ["analyze_spending", "check_budgets", "suggest_budget", "predict_overrun"],
            },
            {
                "name": "fraud_sentinel",
                "description": "Detects fraudulent transactions and suspicious activity",
                "capabilities": ["analyze_transaction", "scan_recent", "get_risk_score"],
            },
            {
                "name": "finance_concierge",
                "description": "Answers general financial questions",
                "capabilities": ["general_query", "delegation"],
            },
            {
                "name": "investment_advisor",
                "description": "Provides investment advice and portfolio analysis",
                "capabilities": ["analyze_portfolio", "suggest_allocation"],
            },
        ]
    }
