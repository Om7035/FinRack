"""Bank accounts API endpoints"""

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.users import User
from app.models.accounts import BankAccount
from app.schemas.accounts import (
    AccountCreate,
    AccountResponse,
    AccountBalance,
    LinkTokenResponse
)
from app.core.deps import get_current_user
from app.services.plaid_service import plaid_service
from app.services.transaction_sync import sync_account_transactions

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create Plaid Link token for connecting bank accounts
    
    Returns a link_token to initialize Plaid Link in the frontend
    """
    try:
        # Get user profile for email
        result = await plaid_service.create_link_token(
            user_id=str(current_user.id),
            user_email=current_user.email,
            webhook_url=f"{settings.APP_URL}/api/webhooks/plaid" if hasattr(settings, 'APP_URL') else None
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create link token: {str(e)}"
        )


@router.post("/link", response_model=List[AccountResponse], status_code=status.HTTP_201_CREATED)
async def link_account(
    account_data: AccountCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Link a new bank account using Plaid public token
    
    - **public_token**: Public token from Plaid Link
    
    This will:
    1. Exchange public token for access token
    2. Fetch account details from Plaid
    3. Create account records in database
    4. Trigger initial transaction sync in background
    """
    try:
        # Exchange public token for access token
        token_data = await plaid_service.exchange_public_token(account_data.public_token)
        access_token = token_data['access_token']
        item_id = token_data['item_id']
        
        # Get accounts from Plaid
        plaid_accounts = await plaid_service.get_accounts(access_token)
        
        # Create account records
        created_accounts = []
        
        for plaid_account in plaid_accounts:
            # Check if account already exists
            result = await db.execute(
                select(BankAccount).where(
                    BankAccount.plaid_account_id == plaid_account['account_id'],
                    BankAccount.user_id == current_user.id
                )
            )
            existing_account = result.scalar_one_or_none()
            
            if existing_account:
                # Update existing account
                existing_account.plaid_access_token = access_token
                existing_account.is_active = True
                existing_account.current_balance = plaid_account['current_balance']
                existing_account.available_balance = plaid_account['available_balance']
                created_accounts.append(existing_account)
            else:
                # Create new account
                new_account = BankAccount(
                    user_id=current_user.id,
                    plaid_account_id=plaid_account['account_id'],
                    plaid_access_token=access_token,
                    plaid_item_id=item_id,
                    name=plaid_account['name'],
                    official_name=plaid_account.get('official_name'),
                    account_type=plaid_account['type'],
                    account_subtype=plaid_account.get('subtype'),
                    mask=plaid_account.get('mask'),
                    current_balance=plaid_account['current_balance'],
                    available_balance=plaid_account.get('available_balance'),
                    limit_amount=plaid_account.get('limit'),
                    currency=plaid_account['currency'],
                    is_active=True,
                    sync_status='pending'
                )
                
                db.add(new_account)
                await db.flush()
                created_accounts.append(new_account)
                
                # Trigger initial transaction sync in background
                background_tasks.add_task(
                    sync_account_transactions.delay,
                    str(new_account.id),
                    str(current_user.id)
                )
        
        await db.commit()
        
        for account in created_accounts:
            await db.refresh(account)
        
        return created_accounts
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link account: {str(e)}"
        )


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all bank accounts for current user
    """
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.user_id == current_user.id)
        .order_by(BankAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific account details
    """
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account


@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current balance for account (fetches from Plaid)
    """
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        # Fetch latest balance from Plaid
        balances = await plaid_service.get_balance(account.plaid_access_token)
        account_balance = balances.get(account.plaid_account_id, {})
        
        # Update database
        account.current_balance = account_balance.get('current', account.current_balance)
        account.available_balance = account_balance.get('available')
        await db.commit()
        
        return {
            'current': account.current_balance,
            'available': account.available_balance,
            'limit': account.limit_amount,
            'currency': account.currency
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch balance: {str(e)}"
        )


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Manually trigger transaction sync for account
    """
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Trigger sync in background
    task = sync_account_transactions.delay(str(account_id), str(current_user.id))
    
    return {
        'message': 'Sync started',
        'account_id': str(account_id),
        'task_id': task.id
    }


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Unlink (deactivate) a bank account
    
    This doesn't delete the account, just marks it as inactive
    """
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.is_active = False
    await db.commit()


# Import settings at the end to avoid circular imports
from app.config import settings
