"""Financial Goals API endpoints"""

from typing import List, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.goals import FinancialGoal, GoalProgress
from app.schemas.goals import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalProgressCreate,
    GoalProgressResponse,
    GoalProjection
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])


async def calculate_goal_projections(goal: FinancialGoal) -> dict:
    """Calculate goal projections and probability of success"""
    remaining_amount = goal.target_amount - goal.current_amount
    
    # Calculate days remaining
    days_remaining = None
    if goal.deadline:
        days_remaining = (goal.deadline - date.today()).days
    
    # Calculate required monthly savings
    required_monthly_savings = None
    if days_remaining and days_remaining > 0:
        months_remaining = days_remaining / 30
        if months_remaining > 0:
            required_monthly_savings = remaining_amount / Decimal(months_remaining)
    
    # Calculate projected completion date (based on current progress rate)
    projected_completion_date = None
    if goal.current_amount > 0:
        days_since_start = (date.today() - goal.start_date).days
        if days_since_start > 0:
            daily_rate = goal.current_amount / Decimal(days_since_start)
            if daily_rate > 0:
                days_to_complete = remaining_amount / daily_rate
                projected_completion_date = date.today() + timedelta(days=int(days_to_complete))
    
    # Calculate probability of success
    probability_of_success = None
    on_track = False
    
    if goal.deadline and projected_completion_date:
        if projected_completion_date <= goal.deadline:
            probability_of_success = Decimal(90)  # High probability
            on_track = True
        else:
            # Calculate how far off track
            days_over = (projected_completion_date - goal.deadline).days
            if days_over < 30:
                probability_of_success = Decimal(70)
            elif days_over < 90:
                probability_of_success = Decimal(50)
            else:
                probability_of_success = Decimal(30)
    elif goal.current_amount >= goal.target_amount:
        probability_of_success = Decimal(100)
        on_track = True
    
    return {
        "remaining_amount": remaining_amount,
        "days_remaining": days_remaining,
        "required_monthly_savings": required_monthly_savings,
        "projected_completion_date": projected_completion_date,
        "probability_of_success": probability_of_success,
        "on_track": on_track
    }


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new financial goal
    
    - **name**: Goal name
    - **target_amount**: Target amount to save
    - **category**: Goal category (emergency_fund, vacation, house, etc.)
    - **description**: Optional description
    - **deadline**: Optional deadline
    - **priority**: high, medium, or low
    - **current_amount**: Starting amount (default 0)
    """
    goal = FinancialGoal(
        user_id=current_user.id,
        name=goal_data.name,
        description=goal_data.description,
        category=goal_data.category,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount,
        deadline=goal_data.deadline,
        priority=goal_data.priority,
        percentage_complete=Decimal(0)
    )
    
    # Calculate initial percentage
    if goal.target_amount > 0:
        goal.percentage_complete = (goal.current_amount / goal.target_amount * 100)
    
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    
    return goal


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    status_filter: str = "active",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all financial goals
    
    - **status_filter**: Filter by status (active, achieved, all)
    """
    query = select(FinancialGoal).where(FinancialGoal.user_id == current_user.id)
    
    if status_filter == "active":
        query = query.where(FinancialGoal.status == "active")
    elif status_filter == "achieved":
        query = query.where(FinancialGoal.status == "achieved")
    
    query = query.order_by(desc(FinancialGoal.priority), desc(FinancialGoal.created_at))
    
    result = await db.execute(query)
    goals = result.scalars().all()
    
    return goals


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific goal details
    """
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return goal


@router.get("/{goal_id}/projections", response_model=GoalProjection)
async def get_goal_projections(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get goal projections and probability of success
    
    Returns:
    - Remaining amount
    - Days remaining
    - Required monthly savings
    - Projected completion date
    - Probability of success
    - Whether on track
    """
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    projections = await calculate_goal_projections(goal)
    
    return {
        "goal_id": goal.id,
        "goal_name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "remaining_amount": projections["remaining_amount"],
        "percentage_complete": goal.percentage_complete,
        "deadline": goal.deadline,
        "days_remaining": projections["days_remaining"],
        "required_monthly_savings": projections["required_monthly_savings"],
        "projected_completion_date": projections["projected_completion_date"],
        "probability_of_success": projections["probability_of_success"],
        "on_track": projections["on_track"]
    }


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update goal details
    """
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Update fields
    if goal_data.name is not None:
        goal.name = goal_data.name
    if goal_data.description is not None:
        goal.description = goal_data.description
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.deadline is not None:
        goal.deadline = goal_data.deadline
    if goal_data.priority is not None:
        goal.priority = goal_data.priority
    if goal_data.status is not None:
        goal.status = goal_data.status
        if goal_data.status == "achieved":
            goal.achieved_at = datetime.utcnow()
    
    # Recalculate percentage
    if goal.target_amount > 0:
        goal.percentage_complete = (goal.current_amount / goal.target_amount * 100)
    
    await db.commit()
    await db.refresh(goal)
    
    return goal


@router.post("/{goal_id}/progress", response_model=GoalProgressResponse, status_code=status.HTTP_201_CREATED)
async def add_goal_progress(
    goal_id: UUID,
    progress_data: GoalProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add progress entry to goal
    
    - **amount**: Amount to add/subtract
    - **description**: Optional description
    - **entry_type**: contribution, withdrawal, or adjustment
    """
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Create progress entry
    progress = GoalProgress(
        goal_id=goal.id,
        amount=progress_data.amount,
        description=progress_data.description,
        entry_type=progress_data.entry_type
    )
    
    db.add(progress)
    
    # Update goal current amount
    if progress_data.entry_type == "contribution":
        goal.current_amount += progress_data.amount
    elif progress_data.entry_type == "withdrawal":
        goal.current_amount -= progress_data.amount
    elif progress_data.entry_type == "adjustment":
        goal.current_amount = progress_data.amount
    
    # Update percentage
    if goal.target_amount > 0:
        goal.percentage_complete = (goal.current_amount / goal.target_amount * 100)
    
    # Check if goal is achieved
    if goal.current_amount >= goal.target_amount and goal.status != "achieved":
        goal.status = "achieved"
        goal.achieved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(progress)
    
    return progress


@router.get("/{goal_id}/progress", response_model=List[GoalProgressResponse])
async def list_goal_progress(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all progress entries for a goal
    """
    # Verify goal belongs to user
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Get progress entries
    result = await db.execute(
        select(GoalProgress)
        .where(GoalProgress.goal_id == goal_id)
        .order_by(desc(GoalProgress.date))
    )
    progress_entries = result.scalars().all()
    
    return progress_entries


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a financial goal
    """
    result = await db.execute(
        select(FinancialGoal).where(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == current_user.id
            )
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    await db.delete(goal)
    await db.commit()
