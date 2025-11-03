"""Subscriptions detection service"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import redis.asyncio as redis
import json

from app.models.transactions import Transaction


async def detect_recurring(db: AsyncSession, window_days: int = 180) -> List[Dict[str, Any]]:
    cache = await redis.from_url("redis://localhost:6379/0")
    key = f"subs:detect:{window_days}"
    if (raw := await cache.get(key)):
        return json.loads(raw)
    start = date.today() - timedelta(days=window_days)
    q = (
        select(Transaction.merchant_name, func.count(Transaction.id), func.avg(func.abs(Transaction.amount)))
        .where(Transaction.date >= start, Transaction.amount < 0)
        .group_by(Transaction.merchant_name)
        .having(func.count(Transaction.id) >= 2)
    )
    rows = (await db.execute(q)).all()

    results: List[Dict[str, Any]] = []
    for merchant, cnt, avg_amount in rows:
        if not merchant:
            continue
        results.append({
            "merchant": merchant,
            "count": int(cnt),
            "avg_monthly_cost": round(float(avg_amount), 2),
        })
    await cache.set(key, json.dumps(results), ex=600)
    return results
