"""Transactions API endpoints with semantic search"""

from typing import List, Any, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.sql import text
from decimal import Decimal
from app.database import get_db
from app.models.users import User
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
from app.schemas.transactions import (
    TransactionResponse,
    TransactionUpdate,
    TransactionFilter,
    TransactionSearch,
    TransactionStats,
    BulkCategorize
)
from app.core.deps import get_current_user
from app.services.categorization import categorization_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    account_id: Optional[UUID] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    merchant_name: Optional[str] = None,
    is_pending: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List transactions with filtering and pagination
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **date_from**: Filter transactions from this date
    - **date_to**: Filter transactions until this date
    - **category**: Filter by category
    - **account_id**: Filter by specific account
    - **min_amount**: Minimum transaction amount
    - **max_amount**: Maximum transaction amount
    - **merchant_name**: Filter by merchant name (partial match)
    - **is_pending**: Filter pending/completed transactions
    """
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
        query = query.where(
            or_(
                Transaction.category == category,
                Transaction.user_category == category
            )
        )
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
    if merchant_name:
        query = query.where(Transaction.merchant_name.ilike(f"%{merchant_name}%"))
    if is_pending is not None:
        query = query.where(Transaction.is_pending == is_pending)
    
    # Order by date descending
    query = query.order_by(desc(Transaction.date), desc(Transaction.created_at))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions


@router.get("/search", response_model=List[TransactionResponse])
async def search_transactions(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Semantic search for transactions using vector similarity
    
    - **query**: Natural language search query
    - **limit**: Maximum number of results
    
    Example queries:
    - "coffee purchases last month"
    - "large transactions over $500"
    - "grocery shopping"
    - "restaurants in downtown"
    """
    # Generate embedding for search query
    query_embedding = categorization_service.generate_embedding(query)
    
    if not query_embedding:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate search embedding"
        )
    
    # Perform vector similarity search
    # Using cosine distance for pgvector
    sql_query = text("""
        SELECT t.* 
        FROM transactions t
        JOIN bank_accounts a ON t.account_id = a.id
        WHERE a.user_id = :user_id
        AND t.embedding IS NOT NULL
        ORDER BY t.embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    result = await db.execute(
        sql_query,
        {
            "user_id": str(current_user.id),
            "query_embedding": str(query_embedding),
            "limit": limit
        }
    )
    
    transactions = result.fetchall()
    
    # Convert to Transaction objects
    transaction_ids = [row[0] for row in transactions]
    
    if not transaction_ids:
        return []
    
    # Fetch full transaction objects
    query_obj = select(Transaction).where(Transaction.id.in_(transaction_ids))
    result = await db.execute(query_obj)
    
    return result.scalars().all()


@router.get("/stats", response_model=TransactionStats)
async def get_transaction_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get transaction statistics for a date range
    
    - **date_from**: Start date (defaults to 30 days ago)
    - **date_to**: End date (defaults to today)
    """
    # Default date range: last 30 days
    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    
    # Get all transactions in date range
    query = select(Transaction).join(BankAccount).where(
        and_(
            BankAccount.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to
        )
    )
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Calculate statistics
    total_transactions = len(transactions)
    total_spent = sum(t.amount for t in transactions if t.amount > 0)
    total_income = abs(sum(t.amount for t in transactions if t.amount < 0))
    net_amount = total_income - total_spent
    
    # Group by category
    by_category = {}
    for t in transactions:
        category = t.user_category or t.category or "Uncategorized"
        if category not in by_category:
            by_category[category] = {"count": 0, "amount": 0}
        by_category[category]["count"] += 1
        by_category[category]["amount"] += float(t.amount)
    
    # Group by month
    by_month = {}
    for t in transactions:
        month_key = t.date.strftime("%Y-%m")
        if month_key not in by_month:
            by_month[month_key] = {"count": 0, "amount": 0}
        by_month[month_key]["count"] += 1
        by_month[month_key]["amount"] += float(t.amount)
    
    average_transaction = total_spent / total_transactions if total_transactions > 0 else 0
    
    return {
        "total_transactions": total_transactions,
        "total_spent": total_spent,
        "total_income": total_income,
        "net_amount": net_amount,
        "by_category": by_category,
        "by_month": by_month,
        "average_transaction": average_transaction
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific transaction details
    """
    query = select(Transaction).join(BankAccount).where(
        and_(
            Transaction.id == transaction_id,
            BankAccount.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update transaction details
    
    - **user_category**: Override automatic categorization
    - **user_notes**: Add notes to transaction
    - **is_hidden**: Hide transaction from views
    """
    query = select(Transaction).join(BankAccount).where(
        and_(
            Transaction.id == transaction_id,
            BankAccount.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update fields
    if transaction_data.user_category is not None:
        transaction.user_category = transaction_data.user_category
    if transaction_data.user_notes is not None:
        transaction.user_notes = transaction_data.user_notes
    if transaction_data.is_hidden is not None:
        transaction.is_hidden = transaction_data.is_hidden
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.post("/bulk-categorize")
async def bulk_categorize_transactions(
    bulk_data: BulkCategorize,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Bulk update category for multiple transactions
    
    - **transaction_ids**: List of transaction IDs
    - **category**: Category to apply to all
    """
    # Verify all transactions belong to user
    query = select(Transaction).join(BankAccount).where(
        and_(
            Transaction.id.in_(bulk_data.transaction_ids),
            BankAccount.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    if len(transactions) != len(bulk_data.transaction_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some transactions not found"
        )
    
    # Update all transactions
    updated_count = 0
    for transaction in transactions:
        transaction.user_category = bulk_data.category
        updated_count += 1
    
    await db.commit()
    
    return {
        "message": f"Updated {updated_count} transactions",
        "updated_count": updated_count
    }


@router.get("/export/csv")
async def export_transactions_csv(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Export transactions to CSV
    
    Returns CSV file with all transactions in date range
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Default date range: last 90 days
    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=90)
    
    # Get transactions
    query = select(Transaction).join(BankAccount).where(
        and_(
            BankAccount.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to
        )
    ).order_by(Transaction.date.desc())
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Date", "Amount", "Merchant", "Category", "Description",
        "Payment Channel", "Pending", "Account ID"
    ])
    
    # Write data
    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            float(t.amount),
            t.merchant_name or "",
            t.user_category or t.category or "Uncategorized",
            t.name,
            t.payment_channel or "",
            "Yes" if t.is_pending else "No",
            str(t.account_id)
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{date_from}_{date_to}.csv"
        }
    )
