"""Subscriptions API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.services.subscriptions_service import detect_recurring

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


@router.get("/")
async def list_subscriptions(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await detect_recurring(db)
