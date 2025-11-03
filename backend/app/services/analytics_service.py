"""Analytics service: forecast, patterns, net worth, tax estimates"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.transactions import Transaction


async def get_spending_trend(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
    start = date.today() - timedelta(days=days)
    q = (
        select(Transaction.date, func.sum(Transaction.amount).label("amount"))
        .where(Transaction.date >= start)
        .group_by(Transaction.date)
        .order_by(Transaction.date)
    )
    rows = (await db.execute(q)).all()
    # Convert Decimal to float and ensure negatives as expenses
    return [{"date": r[0].isoformat(), "amount": float(r[1])} for r in rows]


async def get_category_breakdown(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
    start = date.today() - timedelta(days=days)
    q = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(Transaction.date >= start)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = (await db.execute(q)).all()
    return [{"name": r[0] or "Uncategorized", "value": float(r[1])} for r in rows]


async def forecast_cash_flow(db: AsyncSession, months: int = 6) -> List[Dict[str, Any]]:
    # Placeholder: simple average of last 90 days as monthly projection
    trend = await get_spending_trend(db, 90)
    avg_daily = (sum(abs(p["amount"]) for p in trend) / max(len(trend), 1)) if trend else 0.0
    result = []
    for i in range(1, months + 1):
        result.append({"month": i, "projected_expenses": round(avg_daily * 30, 2)})
    return result


async def compute_net_worth(db: AsyncSession) -> Dict[str, float]:
    # Placeholder: expenses negative, income positive; sum as cash position
    q = select(func.sum(Transaction.amount))
    total = (await db.execute(q)).scalar() or 0
    return {"net_worth": float(total)}


async def estimate_tax(db: AsyncSession, rate: float = 0.22) -> Dict[str, float]:
    # Placeholder: income = positive amounts for current year
    start = date(date.today().year, 1, 1)
    q = (
        select(func.sum(Transaction.amount))
        .where(Transaction.date >= start, Transaction.amount > 0)
    )
    income = (await db.execute(q)).scalar() or 0
    estimated = float(income) * rate
    return {"year_income": float(income), "estimated_tax": round(estimated, 2), "rate": rate}
