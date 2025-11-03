"""Budget API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.accounts import BankAccount
from app.models.budgets import Budget
from app.models.transactions import Transaction
from app.schemas.budgets import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetProgress
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Budget:
    """Create a new budget"""
    budget = Budget(
        user_id=current_user.id,
        **budget_data.model_dump()
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.get("", response_model=List[BudgetResponse])
async def list_budgets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Budget]:
    """List all user budgets"""
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .order_by(Budget.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Budget:
    """Get specific budget"""
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: str,
    update_data: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Budget:
    """Update budget"""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    
    await db.commit()
    await db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete budget"""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    
    await db.delete(budget)
    await db.commit()


@router.get("/{budget_id}/progress", response_model=BudgetProgress)
async def get_budget_progress(
    budget_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get budget progress and spending"""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    
    # Calculate spent amount
    spent_result = await db.execute(
        select(func.sum(Transaction.amount))
        .join(BankAccount)
        .where(
            BankAccount.user_id == current_user.id,
            Transaction.category == budget.category,
            Transaction.date >= budget.start_date,
            Transaction.date <= (budget.end_date or date.today()),
            Transaction.amount > 0  # Only expenses
        )
    )
    spent = spent_result.scalar() or Decimal(0)
    
    remaining = budget.amount - spent
    percentage_used = float((spent / budget.amount) * 100) if budget.amount > 0 else 0
    is_exceeded = spent > budget.amount
    
    # Calculate days remaining
    days_remaining = None
    if budget.end_date:
        days_remaining = (budget.end_date - date.today()).days
    
    return {
        'budget': budget,
        'spent': spent,
        'remaining': remaining,
        'percentage_used': percentage_used,
        'is_exceeded': is_exceeded,
        'days_remaining': days_remaining,
    }
