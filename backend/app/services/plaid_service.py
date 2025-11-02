"""Plaid integration service for bank account connections and transactions"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.exceptions import ApiException
from app.config import settings

logger = logging.getLogger(__name__)


class PlaidService:
    """Service for interacting with Plaid API"""
    
    def __init__(self):
        """Initialize Plaid client"""
        configuration = Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_SECRET,
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        # Parse products and country codes
        self.products = [
            Products(p.strip()) 
            for p in settings.PLAID_PRODUCTS.split(',')
        ]
        self.country_codes = [
            CountryCode(c.strip()) 
            for c in settings.PLAID_COUNTRY_CODES.split(',')
        ]
    
    def _get_plaid_host(self) -> str:
        """Get Plaid API host based on environment"""
        env_map = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com',
        }
        return env_map.get(settings.PLAID_ENV, 'https://sandbox.plaid.com')
    
    async def create_link_token(
        self,
        user_id: str,
        user_email: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a link token for Plaid Link initialization
        
        Args:
            user_id: Unique user identifier
            user_email: User's email address
            webhook_url: Optional webhook URL for updates
            
        Returns:
            Dictionary with link_token and expiration
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                client_name=settings.APP_NAME,
                products=self.products,
                country_codes=self.country_codes,
                language='en',
                webhook=webhook_url,
            )
            
            response = self.client.link_token_create(request)
            
            logger.info(f"Link token created for user {user_id}")
            
            return {
                'link_token': response['link_token'],
                'expiration': response['expiration'],
            }
            
        except ApiException as e:
            logger.error(f"Failed to create link token: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """
        Exchange public token for access token
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            Dictionary with access_token and item_id
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            logger.info(f"Public token exchanged for item {response['item_id']}")
            
            return {
                'access_token': response['access_token'],
                'item_id': response['item_id'],
            }
            
        except ApiException as e:
            logger.error(f"Failed to exchange public token: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get all accounts for an access token
        
        Args:
            access_token: Plaid access token
            
        Returns:
            List of account dictionaries
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            accounts = []
            for account in response['accounts']:
                accounts.append({
                    'account_id': account['account_id'],
                    'name': account['name'],
                    'official_name': account.get('official_name'),
                    'type': account['type'],
                    'subtype': account.get('subtype'),
                    'mask': account.get('mask'),
                    'current_balance': account['balances']['current'],
                    'available_balance': account['balances'].get('available'),
                    'limit': account['balances'].get('limit'),
                    'currency': account['balances']['iso_currency_code'] or 'USD',
                })
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except ApiException as e:
            logger.error(f"Failed to get accounts: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    async def get_balance(self, access_token: str) -> Dict[str, Any]:
        """
        Get current balance for all accounts
        
        Args:
            access_token: Plaid access token
            
        Returns:
            Dictionary with account balances
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            balances = {}
            for account in response['accounts']:
                balances[account['account_id']] = {
                    'current': account['balances']['current'],
                    'available': account['balances'].get('available'),
                    'limit': account['balances'].get('limit'),
                    'currency': account['balances']['iso_currency_code'] or 'USD',
                }
            
            logger.info(f"Retrieved balances for {len(balances)} accounts")
            return balances
            
        except ApiException as e:
            logger.error(f"Failed to get balance: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a date range
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions
            end_date: End date for transactions
            account_ids: Optional list of account IDs to filter
            
        Returns:
            List of transaction dictionaries
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                options={'account_ids': account_ids} if account_ids else None
            )
            
            response = self.client.transactions_get(request)
            transactions = []
            
            for txn in response['transactions']:
                transactions.append(self._parse_transaction(txn))
            
            # Handle pagination
            total_transactions = response['total_transactions']
            while len(transactions) < total_transactions:
                request.options = {
                    'offset': len(transactions),
                    'account_ids': account_ids
                } if account_ids else {'offset': len(transactions)}
                
                response = self.client.transactions_get(request)
                for txn in response['transactions']:
                    transactions.append(self._parse_transaction(txn))
            
            logger.info(f"Retrieved {len(transactions)} transactions")
            return transactions
            
        except ApiException as e:
            logger.error(f"Failed to get transactions: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    async def sync_transactions(
        self,
        access_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync transactions using the Transactions Sync API (incremental updates)
        
        Args:
            access_token: Plaid access token
            cursor: Optional cursor for pagination
            
        Returns:
            Dictionary with added, modified, removed transactions and next cursor
            
        Raises:
            ApiException: If Plaid API call fails
        """
        try:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor
            )
            
            response = self.client.transactions_sync(request)
            
            result = {
                'added': [self._parse_transaction(txn) for txn in response['added']],
                'modified': [self._parse_transaction(txn) for txn in response['modified']],
                'removed': [txn['transaction_id'] for txn in response['removed']],
                'next_cursor': response['next_cursor'],
                'has_more': response['has_more'],
            }
            
            logger.info(
                f"Synced transactions: {len(result['added'])} added, "
                f"{len(result['modified'])} modified, {len(result['removed'])} removed"
            )
            
            return result
            
        except ApiException as e:
            logger.error(f"Failed to sync transactions: {e}")
            raise Exception(f"Plaid API error: {e}")
    
    def _parse_transaction(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Plaid transaction into our format"""
        return {
            'transaction_id': txn['transaction_id'],
            'account_id': txn['account_id'],
            'amount': float(txn['amount']),
            'currency': txn.get('iso_currency_code', 'USD'),
            'date': txn['date'],
            'authorized_date': txn.get('authorized_date'),
            'name': txn['name'],
            'merchant_name': txn.get('merchant_name'),
            'merchant_entity_id': txn.get('merchant_entity_id'),
            'category': txn['category'][0] if txn.get('category') else None,
            'category_detailed': ', '.join(txn['category']) if txn.get('category') else None,
            'payment_channel': txn.get('payment_channel'),
            'is_pending': txn.get('pending', False),
            'location': {
                'address': txn.get('location', {}).get('address'),
                'city': txn.get('location', {}).get('city'),
                'region': txn.get('location', {}).get('region'),
                'postal_code': txn.get('location', {}).get('postal_code'),
                'country': txn.get('location', {}).get('country'),
                'lat': txn.get('location', {}).get('lat'),
                'lon': txn.get('location', {}).get('lon'),
            },
            'payment_meta': txn.get('payment_meta', {}),
            'transaction_type': txn.get('transaction_type'),
        }
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Plaid webhook events
        
        Args:
            webhook_data: Webhook payload from Plaid
            
        Returns:
            Dictionary with webhook processing result
        """
        webhook_type = webhook_data.get('webhook_type')
        webhook_code = webhook_data.get('webhook_code')
        item_id = webhook_data.get('item_id')
        
        logger.info(f"Received webhook: {webhook_type}.{webhook_code} for item {item_id}")
        
        # Handle different webhook types
        if webhook_type == 'TRANSACTIONS':
            if webhook_code in ['INITIAL_UPDATE', 'HISTORICAL_UPDATE', 'DEFAULT_UPDATE']:
                # Trigger transaction sync
                return {
                    'action': 'sync_transactions',
                    'item_id': item_id,
                    'webhook_code': webhook_code
                }
            elif webhook_code == 'TRANSACTIONS_REMOVED':
                # Handle removed transactions
                removed_transactions = webhook_data.get('removed_transactions', [])
                return {
                    'action': 'remove_transactions',
                    'item_id': item_id,
                    'removed_transactions': removed_transactions
                }
        
        elif webhook_type == 'ITEM':
            if webhook_code == 'ERROR':
                # Handle item error
                error = webhook_data.get('error', {})
                return {
                    'action': 'handle_error',
                    'item_id': item_id,
                    'error': error
                }
            elif webhook_code == 'PENDING_EXPIRATION':
                # Handle pending expiration
                return {
                    'action': 'notify_expiration',
                    'item_id': item_id
                }
        
        return {
            'action': 'unknown',
            'webhook_type': webhook_type,
            'webhook_code': webhook_code
        }


# Global Plaid service instance
plaid_service = PlaidService()
