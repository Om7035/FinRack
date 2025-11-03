"""Bank account API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.users import User
from app.models.accounts import BankAccount
from app.schemas.accounts import AccountResponse, AccountCreate, LinkTokenResponse
from app.core.deps import get_current_active_user
from app.services.plaid_service import plaid_service
from app.services.transaction_sync import initial_transaction_sync, sync_account_transactions

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Create Plaid Link token for connecting bank accounts"""
    try:
        result = await plaid_service.create_link_token(
            user_id=str(current_user.id),
            user_email=current_user.email,
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BankAccount]:
    """Exchange public token and link bank accounts"""
    try:
        # Exchange public token
        exchange_result = await plaid_service.exchange_public_token(
            account_data.public_token
        )
        
        access_token = exchange_result['access_token']
        item_id = exchange_result['item_id']
        
        # Get accounts from Plaid
        plaid_accounts = await plaid_service.get_accounts(access_token)
        
        # Create account records
        created_accounts = []
        for plaid_account in plaid_accounts:
            account = BankAccount(
                user_id=current_user.id,
                plaid_account_id=plaid_account['account_id'],
                plaid_access_token=access_token,
                plaid_item_id=item_id,
                name=plaid_account['name'],
                official_name=plaid_account.get('official_name'),
                account_type=plaid_account['type'],
                account_subtype=plaid_account.get('subtype'),
                current_balance=plaid_account['current_balance'],
                available_balance=plaid_account['available_balance'],
                currency=plaid_account['currency'],
                mask=plaid_account.get('mask'),
            )
            db.add(account)
            created_accounts.append(account)
        
        await db.flush()
        
        # Queue initial transaction sync for each account
        for account in created_accounts:
            await initial_transaction_sync(db, account)
        
        await db.commit()
        
        return created_accounts
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link account: {str(e)}"
        )


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BankAccount]:
    """Get all user's bank accounts"""
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.user_id == current_user.id)
        .order_by(BankAccount.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BankAccount:
    """Get specific account details"""
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


@router.get("/{account_id}/balance", response_model=dict)
async def get_account_balance(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get current account balance from Plaid"""
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
        accounts = await plaid_service.get_accounts(account.plaid_access_token)
        plaid_account = next(
            (a for a in accounts if a['account_id'] == account.plaid_account_id),
            None
        )
        
        if plaid_account:
            # Update stored balance
            account.current_balance = plaid_account['current_balance']
            account.available_balance = plaid_account['available_balance']
            await db.commit()
            
            return {
                'current_balance': plaid_account['current_balance'],
                'available_balance': plaid_account['available_balance'],
                'currency': plaid_account['currency'],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found in Plaid"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}"
        )


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Manually trigger account sync"""
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
    
    # Queue sync task
    sync_account_transactions.delay(account_id)
    
    return {
        'message': 'Sync queued successfully',
        'account_id': account_id,
    }


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Unlink (soft delete) a bank account"""
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
    
    # Soft delete
    account.is_active = False
    await db.commit()
