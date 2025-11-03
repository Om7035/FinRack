"""Transaction API endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date, datetime
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
from app.schemas.transactions import (
    TransactionResponse,
    TransactionUpdate,
    TransactionSearchRequest,
    TransactionStats
)
from app.core.deps import get_current_active_user
from app.services.categorization import categorizer

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    account_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Transaction]:
    """List transactions with filters and pagination"""
    # Build query
    query = select(Transaction).join(BankAccount).where(
        BankAccount.user_id == current_user.id
    )
    
    # Apply filters
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if category:
        query = query.where(Transaction.category == category)
    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    
    # Order and paginate
    query = query.order_by(Transaction.date.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Transaction:
    """Get specific transaction"""
    result = await db.execute(
        select(Transaction)
        .join(BankAccount)
        .where(
            Transaction.id == transaction_id,
            BankAccount.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Transaction:
    """Update transaction (category, notes)"""
    result = await db.execute(
        select(Transaction)
        .join(BankAccount)
        .where(
            Transaction.id == transaction_id,
            BankAccount.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update fields
    if update_data.category is not None:
        transaction.category = update_data.category
    if update_data.notes is not None:
        transaction.notes = update_data.notes
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.post("/search", response_model=List[TransactionResponse])
async def semantic_search(
    search_request: TransactionSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Transaction]:
    """Semantic search transactions using embeddings"""
    # Generate query embedding
    query_embedding = categorizer.generate_embedding(search_request.query)
    
    # Vector similarity search using pgvector
    # Note: This uses cosine distance (<=>)
    result = await db.execute(
        select(Transaction)
        .join(BankAccount)
        .where(BankAccount.user_id == current_user.id)
        .order_by(Transaction.embedding.cosine_distance(query_embedding))
        .limit(search_request.limit)
    )
    
    return result.scalars().all()


@router.get("/stats/summary", response_model=TransactionStats)
async def get_transaction_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get transaction statistics"""
    # Build base query
    query = select(Transaction).join(BankAccount).where(
        BankAccount.user_id == current_user.id
    )
    
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    
    # Total transactions
    count_result = await db.execute(
        select(func.count(Transaction.id)).select_from(query.subquery())
    )
    total_transactions = count_result.scalar()
    
    # Total spent (positive amounts)
    spent_result = await db.execute(
        select(func.sum(Transaction.amount))
        .select_from(query.where(Transaction.amount > 0).subquery())
    )
    total_spent = spent_result.scalar() or Decimal(0)
    
    # Total income (negative amounts in Plaid)
    income_result = await db.execute(
        select(func.sum(Transaction.amount))
        .select_from(query.where(Transaction.amount < 0).subquery())
    )
    total_income = abs(income_result.scalar() or Decimal(0))
    
    # By category
    category_result = await db.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        )
        .select_from(query.subquery())
        .group_by(Transaction.category)
    )
    by_category = {row[0] or 'Uncategorized': float(row[1]) for row in category_result}
    
    # By month
    month_result = await db.execute(
        select(
            func.to_char(Transaction.date, 'YYYY-MM').label('month'),
            func.sum(Transaction.amount).label('total')
        )
        .select_from(query.subquery())
        .group_by('month')
        .order_by('month')
    )
    by_month = {row[0]: float(row[1]) for row in month_result}
    
    return {
        'total_transactions': total_transactions,
        'total_spent': total_spent,
        'total_income': total_income,
        'by_category': by_category,
        'by_month': by_month,
    }


@router.post("/bulk-categorize")
async def bulk_categorize(
    transaction_ids: List[str],
    category: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Bulk update transaction categories"""
    result = await db.execute(
        select(Transaction)
        .join(BankAccount)
        .where(
            Transaction.id.in_(transaction_ids),
            BankAccount.user_id == current_user.id
        )
    )
    transactions = result.scalars().all()
    
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found"
        )
    
    for transaction in transactions:
        transaction.category = category
    
    await db.commit()
    
    return {
        'message': f'Updated {len(transactions)} transactions',
        'count': len(transactions),
    }
