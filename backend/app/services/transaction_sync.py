"""Transaction synchronization service with Celery tasks"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.accounts import BankAccount
from app.models.transactions import Transaction
from app.services.plaid_service import plaid_service
from app.services.categorization import categorization_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.services.transaction_sync.sync_account_transactions")
def sync_account_transactions(account_id: str, user_id: str) -> Dict[str, Any]:
    """
    Celery task to sync transactions for a single account
    
    Args:
        account_id: Bank account ID (UUID as string)
        user_id: User ID (UUID as string)
        
    Returns:
        Dictionary with sync results
    """
    import asyncio
    return asyncio.run(_sync_account_transactions_async(account_id, user_id))


async def _sync_account_transactions_async(
    account_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Async implementation of transaction sync"""
    async with AsyncSessionLocal() as db:
        try:
            # Get account from database
            result = await db.execute(
                select(BankAccount).where(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                logger.error(f"Account {account_id} not found")
                return {'error': 'Account not found'}
            
            # Update sync status
            account.sync_status = 'syncing'
            await db.commit()
            
            # Sync transactions from Plaid
            try:
                # Use incremental sync if we have transactions
                result = await db.execute(
                    select(Transaction)
                    .where(Transaction.account_id == account_id)
                    .order_by(Transaction.date.desc())
                    .limit(1)
                )
                latest_transaction = result.scalar_one_or_none()
                
                if latest_transaction:
                    # Incremental sync
                    sync_result = await plaid_service.sync_transactions(
                        access_token=account.plaid_access_token
                    )
                    
                    added_count = await _process_added_transactions(
                        db, account, sync_result['added']
                    )
                    modified_count = await _process_modified_transactions(
                        db, account, sync_result['modified']
                    )
                    removed_count = await _process_removed_transactions(
                        db, sync_result['removed']
                    )
                    
                else:
                    # Initial sync - get last 90 days
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=90)
                    
                    transactions = await plaid_service.get_transactions(
                        access_token=account.plaid_access_token,
                        start_date=start_date,
                        end_date=end_date,
                        account_ids=[account.plaid_account_id]
                    )
                    
                    added_count = await _process_added_transactions(
                        db, account, transactions
                    )
                    modified_count = 0
                    removed_count = 0
                
                # Update account balance
                balances = await plaid_service.get_balance(account.plaid_access_token)
                account_balance = balances.get(account.plaid_account_id, {})
                
                account.current_balance = account_balance.get('current', account.current_balance)
                account.available_balance = account_balance.get('available')
                account.sync_status = 'success'
                account.last_synced_at = datetime.utcnow()
                account.sync_error = None
                
                await db.commit()
                
                logger.info(
                    f"Synced account {account_id}: "
                    f"{added_count} added, {modified_count} modified, {removed_count} removed"
                )
                
                return {
                    'success': True,
                    'account_id': account_id,
                    'added': added_count,
                    'modified': modified_count,
                    'removed': removed_count,
                }
                
            except Exception as e:
                logger.error(f"Failed to sync transactions for account {account_id}: {e}")
                account.sync_status = 'error'
                account.sync_error = str(e)
                await db.commit()
                
                return {
                    'success': False,
                    'account_id': account_id,
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"Database error during sync: {e}")
            return {
                'success': False,
                'account_id': account_id,
                'error': str(e)
            }


async def _process_added_transactions(
    db: AsyncSession,
    account: BankAccount,
    transactions: List[Dict[str, Any]]
) -> int:
    """Process newly added transactions"""
    added_count = 0
    
    for txn_data in transactions:
        # Check if transaction already exists
        result = await db.execute(
            select(Transaction).where(
                Transaction.plaid_transaction_id == txn_data['transaction_id']
            )
        )
        existing_txn = result.scalar_one_or_none()
        
        if existing_txn:
            continue  # Skip duplicates
        
        # Categorize transaction
        category, confidence = categorization_service.categorize_transaction(
            description=txn_data['name'],
            merchant_name=txn_data.get('merchant_name'),
            plaid_category=txn_data.get('category'),
            amount=txn_data['amount']
        )
        
        # Generate embedding for semantic search
        embedding_text = f"{txn_data['name']} {txn_data.get('merchant_name', '')}"
        embedding = categorization_service.generate_embedding(embedding_text)
        
        # Create transaction
        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id=txn_data['transaction_id'],
            amount=txn_data['amount'],
            currency=txn_data['currency'],
            date=txn_data['date'],
            authorized_date=txn_data.get('authorized_date'),
            name=txn_data['name'],
            original_description=txn_data['name'],
            merchant_name=txn_data.get('merchant_name'),
            merchant_entity_id=txn_data.get('merchant_entity_id'),
            category=category,
            category_detailed=txn_data.get('category_detailed'),
            category_confidence=confidence,
            location_address=txn_data['location'].get('address'),
            location_city=txn_data['location'].get('city'),
            location_region=txn_data['location'].get('region'),
            location_postal_code=txn_data['location'].get('postal_code'),
            location_country=txn_data['location'].get('country'),
            location_lat=txn_data['location'].get('lat'),
            location_lon=txn_data['location'].get('lon'),
            payment_channel=txn_data.get('payment_channel'),
            transaction_type=txn_data.get('transaction_type'),
            is_pending=txn_data['is_pending'],
            embedding=embedding,
        )
        
        db.add(transaction)
        added_count += 1
    
    await db.commit()
    return added_count


async def _process_modified_transactions(
    db: AsyncSession,
    account: BankAccount,
    transactions: List[Dict[str, Any]]
) -> int:
    """Process modified transactions"""
    modified_count = 0
    
    for txn_data in transactions:
        result = await db.execute(
            select(Transaction).where(
                Transaction.plaid_transaction_id == txn_data['transaction_id']
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            continue
        
        # Update transaction fields
        transaction.amount = txn_data['amount']
        transaction.date = txn_data['date']
        transaction.authorized_date = txn_data.get('authorized_date')
        transaction.name = txn_data['name']
        transaction.merchant_name = txn_data.get('merchant_name')
        transaction.is_pending = txn_data['is_pending']
        
        # Re-categorize if needed
        if not transaction.user_category:  # Don't override user categories
            category, confidence = categorization_service.categorize_transaction(
                description=txn_data['name'],
                merchant_name=txn_data.get('merchant_name'),
                plaid_category=txn_data.get('category'),
                amount=txn_data['amount']
            )
            transaction.category = category
            transaction.category_confidence = confidence
        
        modified_count += 1
    
    await db.commit()
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
    
    await db.commit()
    return removed_count


@celery_app.task(name="app.services.transaction_sync.sync_all_accounts")
def sync_all_accounts() -> Dict[str, Any]:
    """
    Celery task to sync all active accounts
    
    This runs periodically (every hour) to keep transactions up to date
    """
    import asyncio
    return asyncio.run(_sync_all_accounts_async())


async def _sync_all_accounts_async() -> Dict[str, Any]:
    """Async implementation of sync all accounts"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active accounts
            result = await db.execute(
                select(BankAccount).where(BankAccount.is_active == True)
            )
            accounts = result.scalars().all()
            
            logger.info(f"Starting sync for {len(accounts)} accounts")
            
            # Trigger sync for each account
            results = []
            for account in accounts:
                try:
                    # Call sync task for each account
                    task_result = sync_account_transactions.delay(
                        str(account.id),
                        str(account.user_id)
                    )
                    results.append({
                        'account_id': str(account.id),
                        'task_id': task_result.id
                    })
                except Exception as e:
                    logger.error(f"Failed to trigger sync for account {account.id}: {e}")
                    results.append({
                        'account_id': str(account.id),
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'total_accounts': len(accounts),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to sync all accounts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
