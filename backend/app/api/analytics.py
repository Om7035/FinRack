"""Analytics API endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.services.analytics_service import (
    get_spending_trend,
    get_category_breakdown,
    forecast_cash_flow,
    compute_net_worth,
    estimate_tax,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/spending-trend")
async def spending_trend(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await get_spending_trend(db, days=days)


@router.get("/category-breakdown")
async def category_breakdown(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await get_category_breakdown(db, days=days)


@router.get("/forecast")
async def forecast(months: int = Query(6, ge=1, le=24), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await forecast_cash_flow(db, months=months)


@router.get("/net-worth")
async def net_worth(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await compute_net_worth(db)


@router.get("/tax-estimate")
async def tax_estimate(rate: float = Query(0.22, ge=0, le=1), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await estimate_tax(db, rate=rate)
