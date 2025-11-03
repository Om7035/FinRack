"""Fraud Sentinel Agent - Real-time fraud detection"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import select, func
from app.agents.base import BaseAgent
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FraudSentinelAgent(BaseAgent):
    """Agent for fraud detection and security monitoring"""
    
    def __init__(self, db):
        super().__init__(
            name="fraud_sentinel",
            description="an AI agent that detects fraudulent transactions and suspicious activity",
            db=db,
        )
        
        self.risk_thresholds = {
            'low': 30,
            'medium': 60,
            'high': 80,
        }
    
    async def _execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute fraud detection task"""
        
        if task_type == "analyze_transaction":
            return await self._analyze_transaction(user_id, input_data)
        elif task_type == "scan_recent":
            return await self._scan_recent_transactions(user_id)
        elif task_type == "get_risk_score":
            return await self._get_account_risk_score(user_id)
        else:
            return await self._general_security_check(user_id)
    
    async def _analyze_transaction(
        self,
        user_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze single transaction for fraud"""
        transaction_data = input_data.get('transaction', {})
        
        # Calculate risk score
        risk_score = await self._calculate_risk_score(user_id, transaction_data)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Get anomaly reasons
        anomalies = await self._detect_anomalies(user_id, transaction_data)
        
        # Generate recommendation
        recommendation = await self._generate_recommendation(risk_score, anomalies)
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "anomalies": anomalies,
            "recommendation": recommendation,
        }
    
    async def _scan_recent_transactions(self, user_id: str) -> Dict[str, Any]:
        """Scan recent transactions for fraud"""
        # Get transactions from last 7 days
        start_date = date.today() - timedelta(days=7)
        
        result = await self.db.execute(
            select(Transaction)
            .join(BankAccount)
            .where(
                BankAccount.user_id == user_id,
                Transaction.date >= start_date,
            )
            .order_by(Transaction.date.desc())
        )
        transactions = result.scalars().all()
        
        suspicious = []
        for txn in transactions:
            txn_data = {
                "amount": float(txn.amount),
                "merchant": txn.merchant_name,
                "category": txn.category,
                "date": str(txn.date),
            }
            
            risk_score = await self._calculate_risk_score(user_id, txn_data)
            
            if risk_score > self.risk_thresholds['medium']:
                suspicious.append({
                    "transaction_id": str(txn.id),
                    "amount": float(txn.amount),
                    "merchant": txn.merchant_name,
                    "date": str(txn.date),
                    "risk_score": risk_score,
                    "risk_level": self._get_risk_level(risk_score),
                })
        
        return {
            "total_scanned": len(transactions),
            "suspicious_count": len(suspicious),
            "suspicious_transactions": suspicious,
        }
    
    async def _calculate_risk_score(
        self,
        user_id: str,
        transaction_data: Dict[str, Any],
    ) -> float:
        """Calculate fraud risk score (0-100)"""
        score = 0.0
        
        amount = transaction_data.get('amount', 0)
        merchant = transaction_data.get('merchant', '')
        
        # Check unusual amount
        avg_amount = await self._get_average_transaction_amount(user_id)
        if amount > avg_amount * 3:
            score += 30
        
        # Check new merchant
        is_new_merchant = await self._is_new_merchant(user_id, merchant)
        if is_new_merchant:
            score += 20
        
        # Check velocity (multiple transactions)
        velocity_score = await self._check_velocity(user_id)
        score += velocity_score
        
        # Check unusual time
        # TODO: Implement time-based checks
        
        return min(score, 100)
    
    async def _get_average_transaction_amount(self, user_id: str) -> Decimal:
        """Get average transaction amount"""
        result = await self.db.execute(
            select(func.avg(Transaction.amount))
            .join(BankAccount)
            .where(
                BankAccount.user_id == user_id,
                Transaction.amount > 0,
            )
        )
        avg = result.scalar()
        return avg or Decimal(0)
    
    async def _is_new_merchant(self, user_id: str, merchant: str) -> bool:
        """Check if merchant is new"""
        if not merchant:
            return False
        
        result = await self.db.execute(
            select(func.count(Transaction.id))
            .join(BankAccount)
            .where(
                BankAccount.user_id == user_id,
                Transaction.merchant_name == merchant,
            )
        )
        count = result.scalar()
        return count <= 1
    
    async def _check_velocity(self, user_id: str) -> float:
        """Check transaction velocity (multiple in short time)"""
        # Get transactions in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        result = await self.db.execute(
            select(func.count(Transaction.id))
            .join(BankAccount)
            .where(
                BankAccount.user_id == user_id,
                Transaction.created_at >= one_hour_ago,
            )
        )
        count = result.scalar()
        
        if count > 5:
            return 30
        elif count > 3:
            return 15
        return 0
    
    async def _detect_anomalies(
        self,
        user_id: str,
        transaction_data: Dict[str, Any],
    ) -> List[str]:
        """Detect specific anomalies"""
        anomalies = []
        
        amount = transaction_data.get('amount', 0)
        avg_amount = await self._get_average_transaction_amount(user_id)
        
        if amount > avg_amount * 3:
            anomalies.append(f"Unusually large amount (${amount} vs avg ${avg_amount})")
        
        merchant = transaction_data.get('merchant', '')
        if await self._is_new_merchant(user_id, merchant):
            anomalies.append(f"New merchant: {merchant}")
        
        return anomalies
    
    async def _generate_recommendation(
        self,
        risk_score: float,
        anomalies: List[str],
    ) -> str:
        """Generate fraud prevention recommendation"""
        if risk_score > self.risk_thresholds['high']:
            return "HIGH RISK: Consider blocking this transaction and contacting your bank immediately."
        elif risk_score > self.risk_thresholds['medium']:
            return "MEDIUM RISK: Review this transaction carefully. If you don't recognize it, report it."
        else:
            return "LOW RISK: Transaction appears normal."
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score >= self.risk_thresholds['high']:
            return "high"
        elif risk_score >= self.risk_thresholds['medium']:
            return "medium"
        return "low"
    
    async def _get_account_risk_score(self, user_id: str) -> Dict[str, Any]:
        """Get overall account risk score"""
        scan_result = await self._scan_recent_transactions(user_id)
        
        suspicious_count = scan_result['suspicious_count']
        total_scanned = scan_result['total_scanned']
        
        risk_percentage = (suspicious_count / total_scanned * 100) if total_scanned > 0 else 0
        
        return {
            "account_risk_score": risk_percentage,
            "risk_level": self._get_risk_level(risk_percentage),
            "suspicious_transactions": suspicious_count,
            "total_transactions": total_scanned,
        }
    
    async def _general_security_check(self, user_id: str) -> Dict[str, Any]:
        """Perform general security check"""
        scan_result = await self._scan_recent_transactions(user_id)
        risk_score = await self._get_account_risk_score(user_id)
        
        # Generate security report using LLM
        context = {
            "scan_result": scan_result,
            "risk_score": risk_score,
        }
        
        report = await self.think(
            prompt="Generate a security report based on the recent transaction analysis.",
            context=context,
        )
        
        return {
            "scan_result": scan_result,
            "risk_score": risk_score,
            "security_report": report,
        }
