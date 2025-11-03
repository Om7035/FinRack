"""Budget Guardian Agent - Autonomous budget management"""
from typing import Dict, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import select, func
from app.agents.base import BaseAgent
from app.models.budgets import Budget
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
from app.services.notification import notification_service
import logging

logger = logging.getLogger(__name__)


class BudgetGuardianAgent(BaseAgent):
    """Agent for budget management and spending analysis"""
    
    def __init__(self, db):
        super().__init__(
            name="budget_guardian",
            description="an AI agent that monitors budgets, analyzes spending patterns, and provides recommendations",
            db=db,
        )
        
        # Register tools
        self.register_tool(
            "get_spending_by_category",
            self._get_spending_by_category,
            "Get total spending by category for a time period"
        )
        self.register_tool(
            "get_budget_status",
            self._get_budget_status,
            "Get current status of all budgets"
        )
        self.register_tool(
            "predict_monthly_spending",
            self._predict_monthly_spending,
            "Predict spending for current month based on trends"
        )
    
    async def _execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute budget guardian task"""
        
        if task_type == "analyze_spending":
            return await self._analyze_spending(user_id, input_data)
        elif task_type == "check_budgets":
            return await self._check_budgets(user_id)
        elif task_type == "suggest_budget":
            return await self._suggest_budget(user_id, input_data)
        elif task_type == "predict_overrun":
            return await self._predict_overrun(user_id)
        else:
            return await self._general_query(user_id, input_data)
    
    async def _analyze_spending(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze spending patterns"""
        # Get spending by category
        spending = await self._get_spending_by_category(user_id, days=30)
        
        # Get budget status
        budget_status = await self._get_budget_status(user_id)
        
        # Predict monthly spending
        predictions = await self._predict_monthly_spending(user_id)
        
        # Generate insights using LLM
        context = {
            "spending_by_category": spending,
            "budget_status": budget_status,
            "predictions": predictions,
        }
        
        insights = await self.think(
            prompt="Analyze the user's spending patterns and provide actionable insights and recommendations.",
            context=context,
        )
        
        # Remember analysis
        await self.remember(
            content=f"Spending analysis: {insights}",
            memory_type="episodic",
            importance="high",
        )
        
        return {
            "spending": spending,
            "budget_status": budget_status,
            "predictions": predictions,
            "insights": insights,
        }
    
    async def _check_budgets(self, user_id: str) -> Dict[str, Any]:
        """Check all budgets for alerts"""
        budget_status = await self._get_budget_status(user_id)
        alerts = []
        
        for budget_info in budget_status:
            percentage = budget_info['percentage_used']
            
            if percentage >= budget_info['alert_threshold']:
                alert = {
                    "budget": budget_info['name'],
                    "category": budget_info['category'],
                    "percentage": percentage,
                    "spent": budget_info['spent'],
                    "amount": budget_info['amount'],
                    "severity": "high" if percentage >= 100 else "medium",
                }
                alerts.append(alert)
                
                # Send notification
                await notification_service.notify_budget_alert(
                    user_id=user_id,
                    user_email="user@example.com",  # TODO: Get from user
                    budget=budget_info,
                    percentage_used=percentage,
                )
        
        return {
            "total_budgets": len(budget_status),
            "alerts": alerts,
            "alert_count": len(alerts),
        }
    
    async def _suggest_budget(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Suggest budget adjustments"""
        # Get historical spending
        spending = await self._get_spending_by_category(user_id, days=90)
        
        # Calculate averages
        suggestions = []
        for category, amount in spending.items():
            avg_monthly = amount / 3  # 90 days = ~3 months
            suggested_budget = avg_monthly * 1.1  # 10% buffer
            
            suggestions.append({
                "category": category,
                "average_monthly_spending": float(avg_monthly),
                "suggested_budget": float(suggested_budget),
                "reasoning": f"Based on 3-month average with 10% buffer",
            })
        
        # Get LLM recommendations
        context = {"spending_data": spending, "suggestions": suggestions}
        recommendations = await self.think(
            prompt="Review these budget suggestions and provide additional recommendations for the user.",
            context=context,
        )
        
        return {
            "suggestions": suggestions,
            "recommendations": recommendations,
        }
    
    async def _predict_overrun(self, user_id: str) -> Dict[str, Any]:
        """Predict budget overruns"""
        predictions = await self._predict_monthly_spending(user_id)
        budget_status = await self._get_budget_status(user_id)
        
        overrun_risks = []
        
        for budget_info in budget_status:
            category = budget_info['category']
            if category in predictions:
                predicted = predictions[category]
                budget_amount = budget_info['amount']
                
                if predicted > budget_amount:
                    overrun_risks.append({
                        "category": category,
                        "budget": float(budget_amount),
                        "predicted": float(predicted),
                        "overrun_amount": float(predicted - budget_amount),
                        "risk_level": "high" if predicted > budget_amount * 1.2 else "medium",
                    })
        
        return {
            "overrun_risks": overrun_risks,
            "risk_count": len(overrun_risks),
        }
    
    async def _general_query(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle general budget queries"""
        query = input_data.get('query', '')
        
        # Get relevant context
        spending = await self._get_spending_by_category(user_id, days=30)
        budget_status = await self._get_budget_status(user_id)
        
        # Recall relevant memories
        memories = await self.recall(query, limit=3)
        
        context = {
            "query": query,
            "spending": spending,
            "budgets": budget_status,
            "memories": memories,
        }
        
        response = await self.think(
            prompt=f"Answer this budget-related question: {query}",
            context=context,
        )
        
        return {"response": response}
    
    # Tool implementations
    
    async def _get_spending_by_category(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Decimal]:
        """Get spending by category"""
        start_date = date.today() - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            )
            .join(BankAccount)
            .where(
                BankAccount.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.amount > 0,  # Only expenses
            )
            .group_by(Transaction.category)
        )
        
        return {row[0] or 'Uncategorized': row[1] for row in result}
    
    async def _get_budget_status(self, user_id: str) -> list:
        """Get status of all budgets"""
        result = await self.db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.is_active == True,
            )
        )
        budgets = result.scalars().all()
        
        status = []
        for budget in budgets:
            # Calculate spent amount
            spent_result = await self.db.execute(
                select(func.sum(Transaction.amount))
                .join(BankAccount)
                .where(
                    BankAccount.user_id == user_id,
                    Transaction.category == budget.category,
                    Transaction.date >= budget.start_date,
                    Transaction.date <= (budget.end_date or date.today()),
                    Transaction.amount > 0,
                )
            )
            spent = spent_result.scalar() or Decimal(0)
            
            percentage = float((spent / budget.amount) * 100) if budget.amount > 0 else 0
            
            status.append({
                "id": str(budget.id),
                "name": budget.name,
                "category": budget.category,
                "amount": float(budget.amount),
                "spent": float(spent),
                "remaining": float(budget.amount - spent),
                "percentage_used": percentage,
                "alert_threshold": budget.alert_threshold,
            })
        
        return status
    
    async def _predict_monthly_spending(self, user_id: str) -> Dict[str, Decimal]:
        """Predict monthly spending by category"""
        # Get last 30 days spending
        days_in_month = date.today().day
        spending = await self._get_spending_by_category(user_id, days=days_in_month)
        
        # Extrapolate to full month
        predictions = {}
        for category, amount in spending.items():
            daily_avg = amount / days_in_month
            predicted_monthly = daily_avg * 30
            predictions[category] = predicted_monthly
        
        return predictions
