"""Transaction synchronization service with Celery tasks"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
from app.services.plaid_service import plaid_service
from app.services.categorization import categorizer
import logging
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name='app.services.transaction_sync.sync_account_transactions')
def sync_account_transactions(account_id: str) -> dict:
    """
    Celery task to sync transactions for a specific account
    
    Args:
        account_id: Bank account ID
        
    Returns:
        Dict with sync results
    """
    return asyncio.run(_sync_account_transactions_async(account_id))


async def _sync_account_transactions_async(account_id: str) -> dict:
    """Async implementation of transaction sync"""
    async with AsyncSessionLocal() as db:
        try:
            # Get account
            result = await db.execute(
                select(BankAccount).where(BankAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account or not account.is_active:
                return {'status': 'error', 'message': 'Account not found or inactive'}
            
            # Sync transactions from Plaid
            cursor = None  # TODO: Store cursor in database for incremental sync
            sync_result = await plaid_service.sync_transactions(
                access_token=account.plaid_access_token,
                cursor=cursor
            )
            
            added_count = 0
            modified_count = 0
            removed_count = 0
            
            # Process added transactions
            if sync_result['added']:
                added_count = await _process_added_transactions(
                    db, account, sync_result['added']
                )
            
            # Process modified transactions
            if sync_result['modified']:
                modified_count = await _process_modified_transactions(
                    db, sync_result['modified']
                )
            
            # Process removed transactions
            if sync_result['removed']:
                removed_count = await _process_removed_transactions(
                    db, sync_result['removed']
                )
            
            # Update account last synced
            account.last_synced = datetime.utcnow()
            await db.commit()
            
            logger.info(
                f"Synced account {account_id}: "
                f"+{added_count} ~{modified_count} -{removed_count}"
            )
            
            return {
                'status': 'success',
                'account_id': account_id,
                'added': added_count,
                'modified': modified_count,
                'removed': removed_count,
            }
            
        except Exception as e:
            logger.error(f"Error syncing account {account_id}: {e}")
            await db.rollback()
            return {'status': 'error', 'message': str(e)}


async def _process_added_transactions(
    db: AsyncSession,
    account: BankAccount,
    transactions: List[dict]
) -> int:
    """Process newly added transactions"""
    added_count = 0
    
    # Batch categorize
    categories = categorizer.batch_categorize(transactions)
    
    for txn, category in zip(transactions, categories):
        # Check if transaction already exists
        result = await db.execute(
            select(Transaction).where(
                Transaction.plaid_transaction_id == txn['transaction_id']
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            continue  # Skip duplicates
        
        # Generate embedding for semantic search
        text = f"{txn.get('merchant_name', '')} {txn['name']}"
        embedding = categorizer.generate_embedding(text)
        
        # Create transaction
        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id=txn['transaction_id'],
            amount=txn['amount'],
            date=datetime.strptime(txn['date'], '%Y-%m-%d').date(),
            authorized_date=datetime.strptime(txn['authorized_date'], '%Y-%m-%d').date() if txn.get('authorized_date') else None,
            name=txn['name'],
            merchant_name=txn.get('merchant_name'),
            category=category,
            category_detailed=txn.get('category_detailed'),
            payment_channel=txn.get('payment_channel'),
            location_address=txn.get('location_address'),
            location_city=txn.get('location_city'),
            location_region=txn.get('location_region'),
            location_postal_code=txn.get('location_postal_code'),
            location_country=txn.get('location_country'),
            location_lat=txn.get('location_lat'),
            location_lon=txn.get('location_lon'),
            embedding=embedding,
        )
        
        db.add(transaction)
        added_count += 1
    
    await db.flush()
    return added_count


async def _process_modified_transactions(
    db: AsyncSession,
    transactions: List[dict]
) -> int:
    """Process modified transactions"""
    modified_count = 0
    
    for txn in transactions:
        result = await db.execute(
            select(Transaction).where(
                Transaction.plaid_transaction_id == txn['transaction_id']
            )
        )
        transaction = result.scalar_one_or_none()
        
        if transaction:
            # Update transaction fields
            transaction.amount = txn['amount']
            transaction.date = datetime.strptime(txn['date'], '%Y-%m-%d').date()
            transaction.name = txn['name']
            transaction.merchant_name = txn.get('merchant_name')
            
            # Re-categorize if needed
            if not transaction.category:
                transaction.category = categorizer.categorize(
                    description=txn['name'],
                    merchant=txn.get('merchant_name'),
                    amount=txn['amount']
                )
            
            modified_count += 1
    
    await db.flush()
    return modified_count


async def _process_removed_transactions(
    db: AsyncSession,
    transaction_ids: List[str]
) -> int:
    """Process removed transactions"""
    removed_count = 0
    
    for txn_id in transaction_ids:
        result = await db.execute(
            select(Transaction).where(
                Transaction.plaid_transaction_id == txn_id
            )
        )
        transaction = result.scalar_one_or_none()
        
        if transaction:
            await db.delete(transaction)
            removed_count += 1
    
    await db.flush()
    return removed_count


@celery_app.task(name='app.services.transaction_sync.sync_all_accounts')
def sync_all_accounts() -> dict:
    """
    Celery task to sync all active accounts
    
    Returns:
        Dict with sync results
    """
    return asyncio.run(_sync_all_accounts_async())


async def _sync_all_accounts_async() -> dict:
    """Async implementation of sync all accounts"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active accounts
            result = await db.execute(
                select(BankAccount).where(BankAccount.is_active == True)
            )
            accounts = result.scalars().all()
            
            logger.info(f"Starting sync for {len(accounts)} accounts")
            
            # Queue sync tasks for each account
            for account in accounts:
                sync_account_transactions.delay(str(account.id))
            
            return {
                'status': 'success',
                'accounts_queued': len(accounts),
            }
            
        except Exception as e:
            logger.error(f"Error queuing account syncs: {e}")
            return {'status': 'error', 'message': str(e)}


async def initial_transaction_sync(
    db: AsyncSession,
    account: BankAccount,
    days_back: int = 90
) -> dict:
    """
    Perform initial transaction sync for a newly linked account
    
    Args:
        db: Database session
        account: Bank account
        days_back: Number of days to fetch historical transactions
        
    Returns:
        Dict with sync results
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get historical transactions
        transactions = await plaid_service.get_transactions(
            access_token=account.plaid_access_token,
            start_date=start_date,
            end_date=end_date,
            account_ids=[account.plaid_account_id]
        )
        
        # Process transactions
        added_count = await _process_added_transactions(db, account, transactions)
        
        # Update account
        account.last_synced = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Initial sync for account {account.id}: {added_count} transactions")
        
        return {
            'status': 'success',
            'transactions_added': added_count,
        }
        
    except Exception as e:
        logger.error(f"Error in initial sync for account {account.id}: {e}")
        await db.rollback()
        return {'status': 'error', 'message': str(e)}
