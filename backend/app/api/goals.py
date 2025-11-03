"""Financial goals API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.goals import FinancialGoal, GoalProgress
from app.schemas.goals import GoalCreate, GoalUpdate, GoalResponse, GoalProgressAdd, GoalProjection
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/api/goals", tags=["Goals"])


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> FinancialGoal:
    """Create a new financial goal"""
    goal = FinancialGoal(user_id=current_user.id, **goal_data.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[FinancialGoal]:
    """List all user goals"""
    result = await db.execute(
        select(FinancialGoal)
        .where(FinancialGoal.user_id == current_user.id)
        .order_by(FinancialGoal.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> FinancialGoal:
    """Get specific goal"""
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    update_data: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> FinancialGoal:
    """Update goal"""
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    
    # Check if goal is achieved
    if goal.current_amount >= goal.target_amount and goal.status != 'achieved':
        goal.status = 'achieved'
        goal.achieved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete goal"""
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    
    await db.delete(goal)
    await db.commit()


@router.post("/{goal_id}/progress", response_model=GoalResponse)
async def add_goal_progress(
    goal_id: str,
    progress_data: GoalProgressAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> FinancialGoal:
    """Add progress to goal"""
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    
    # Add progress entry
    progress = GoalProgress(
        goal_id=goal.id,
        amount=progress_data.amount,
        notes=progress_data.notes
    )
    db.add(progress)
    
    # Update goal current amount
    goal.current_amount += progress_data.amount
    
    # Check if achieved
    if goal.current_amount >= goal.target_amount:
        goal.status = 'achieved'
        goal.achieved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/{goal_id}/projections", response_model=GoalProjection)
async def get_goal_projections(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get goal projections and probability"""
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    
    # Calculate metrics
    amount_remaining = goal.target_amount - goal.current_amount
    percentage_complete = float((goal.current_amount / goal.target_amount) * 100)
    
    days_until_deadline = None
    required_monthly_savings = None
    projected_completion_date = None
    probability_of_success = None
    on_track = False
    
    if goal.deadline:
        days_until_deadline = (goal.deadline - date.today()).days
        
        if days_until_deadline > 0:
            months_remaining = days_until_deadline / 30
            required_monthly_savings = amount_remaining / months_remaining if months_remaining > 0 else amount_remaining
            
            # Simple probability calculation (can be enhanced with ML)
            if goal.current_amount > 0:
                days_elapsed = (date.today() - goal.created_at.date()).days
                if days_elapsed > 0:
                    daily_rate = goal.current_amount / days_elapsed
                    projected_days = amount_remaining / daily_rate if daily_rate > 0 else float('inf')
                    projected_completion_date = date.today() + timedelta(days=int(projected_days))
                    
                    # Probability based on pace
                    pace_ratio = days_elapsed / (days_elapsed + days_until_deadline)
                    progress_ratio = percentage_complete / 100
                    probability_of_success = min(100, (progress_ratio / pace_ratio) * 100) if pace_ratio > 0 else 0
                    on_track = progress_ratio >= pace_ratio
    
    return {
        'goal': goal,
        'percentage_complete': percentage_complete,
        'amount_remaining': amount_remaining,
        'days_until_deadline': days_until_deadline,
        'required_monthly_savings': required_monthly_savings,
        'projected_completion_date': projected_completion_date,
        'probability_of_success': probability_of_success,
        'on_track': on_track,
    }
