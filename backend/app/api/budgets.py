"""Budgets API endpoints"""

from typing import List, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.budgets import Budget, BudgetAlert
from app.models.transactions import Transaction
from app.models.accounts import BankAccount
from app.schemas.budgets import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetProgress
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


async def calculate_budget_spent(
    db: AsyncSession,
    budget: Budget,
    user_id: UUID
) -> Decimal:
    """Calculate current spent amount for a budget"""
    # Get transactions in budget period and category
    query = select(func.sum(Transaction.amount)).join(BankAccount).where(
        and_(
            BankAccount.user_id == user_id,
            Transaction.date >= budget.start_date,
            Transaction.date <= (budget.end_date or date.today()),
            or_(
                Transaction.category == budget.category,
                Transaction.user_category == budget.category
            ),
            Transaction.amount > 0  # Only expenses
        )
    )
    
    result = await db.execute(query)
    total = result.scalar()
    
    return Decimal(total or 0)


async def update_budget_calculations(
    db: AsyncSession,
    budget: Budget,
    user_id: UUID
) -> None:
    """Update budget calculations"""
    # Calculate current spent
    current_spent = await calculate_budget_spent(db, budget, user_id)
    
    budget.current_spent = current_spent
    budget.remaining = budget.amount - current_spent
    budget.percentage_used = (current_spent / budget.amount * 100) if budget.amount > 0 else 0
    budget.last_calculated_at = datetime.utcnow()
    
    # Check for alerts
    if budget.alert_enabled and budget.percentage_used >= budget.alert_threshold:
        # Create alert if not already exists
        alert_query = select(BudgetAlert).where(
            and_(
                BudgetAlert.budget_id == budget.id,
                BudgetAlert.is_triggered == True,
                BudgetAlert.is_acknowledged == False
            )
        )
        result = await db.execute(alert_query)
        existing_alert = result.scalar_one_or_none()
        
        if not existing_alert:
            alert_type = "exceeded" if budget.percentage_used >= 100 else "warning"
            alert = BudgetAlert(
                budget_id=budget.id,
                alert_type=alert_type,
                threshold=budget.percentage_used,
                message=f"Budget '{budget.name}' is at {budget.percentage_used:.1f}% ({budget.current_spent}/{budget.amount})",
                is_triggered=True,
                triggered_at=datetime.utcnow()
            )
            db.add(alert)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new budget
    
    - **name**: Budget name
    - **category**: Category to track
    - **amount**: Budget amount
    - **period**: weekly, monthly, yearly, or custom
    - **start_date**: Budget start date
    - **end_date**: Budget end date (optional for recurring budgets)
    - **alert_threshold**: Percentage to trigger alert (default 80%)
    """
    # Calculate end date based on period if not provided
    end_date = budget_data.end_date
    if not end_date:
        if budget_data.period == "weekly":
            end_date = budget_data.start_date + timedelta(days=7)
        elif budget_data.period == "monthly":
            end_date = budget_data.start_date + timedelta(days=30)
        elif budget_data.period == "yearly":
            end_date = budget_data.start_date + timedelta(days=365)
    
    # Create budget
    budget = Budget(
        user_id=current_user.id,
        name=budget_data.name,
        category=budget_data.category,
        amount=budget_data.amount,
        period=budget_data.period,
        start_date=budget_data.start_date,
        end_date=end_date,
        alert_threshold=budget_data.alert_threshold,
        current_spent=Decimal(0),
        remaining=budget_data.amount,
        percentage_used=Decimal(0)
    )
    
    db.add(budget)
    await db.flush()
    
    # Calculate initial spent
    await update_budget_calculations(db, budget, current_user.id)
    
    await db.commit()
    await db.refresh(budget)
    
    return budget


@router.get("", response_model=List[BudgetResponse])
async def list_budgets(
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all budgets for current user
    
    - **is_active**: Filter by active/inactive budgets
    """
    query = select(Budget).where(
        and_(
            Budget.user_id == current_user.id,
            Budget.is_active == is_active
        )
    ).order_by(Budget.created_at.desc())
    
    result = await db.execute(query)
    budgets = result.scalars().all()
    
    # Update calculations for all budgets
    for budget in budgets:
        await update_budget_calculations(db, budget, current_user.id)
    
    await db.commit()
    
    return budgets


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific budget details
    """
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.user_id == current_user.id
            )
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Update calculations
    await update_budget_calculations(db, budget, current_user.id)
    await db.commit()
    
    return budget


@router.get("/{budget_id}/progress", response_model=BudgetProgress)
async def get_budget_progress(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get detailed budget progress with transaction count
    """
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.user_id == current_user.id
            )
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Update calculations
    await update_budget_calculations(db, budget, current_user.id)
    await db.commit()
    
    # Get transaction count
    count_query = select(func.count(Transaction.id)).join(BankAccount).where(
        and_(
            BankAccount.user_id == current_user.id,
            Transaction.date >= budget.start_date,
            Transaction.date <= (budget.end_date or date.today()),
            or_(
                Transaction.category == budget.category,
                Transaction.user_category == budget.category
            )
        )
    )
    
    result = await db.execute(count_query)
    transactions_count = result.scalar()
    
    # Calculate days remaining
    days_remaining = 0
    if budget.end_date:
        days_remaining = (budget.end_date - date.today()).days
    
    return {
        "budget_id": budget.id,
        "budget_name": budget.name,
        "category": budget.category,
        "amount": budget.amount,
        "current_spent": budget.current_spent,
        "remaining": budget.remaining,
        "percentage_used": budget.percentage_used,
        "is_exceeded": budget.current_spent > budget.amount,
        "is_warning": budget.percentage_used >= budget.alert_threshold,
        "days_remaining": days_remaining,
        "transactions_count": transactions_count
    }


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update budget details
    
    - **name**: Update budget name
    - **amount**: Update budget amount
    - **alert_threshold**: Update alert threshold
    - **is_active**: Activate/deactivate budget
    """
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.user_id == current_user.id
            )
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Update fields
    if budget_data.name is not None:
        budget.name = budget_data.name
    if budget_data.amount is not None:
        budget.amount = budget_data.amount
    if budget_data.alert_threshold is not None:
        budget.alert_threshold = budget_data.alert_threshold
    if budget_data.is_active is not None:
        budget.is_active = budget_data.is_active
    
    # Recalculate
    await update_budget_calculations(db, budget, current_user.id)
    
    await db.commit()
    await db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a budget
    """
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.user_id == current_user.id
            )
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    await db.delete(budget)
    await db.commit()


# Import at the end to avoid circular imports
from sqlalchemy import or_
