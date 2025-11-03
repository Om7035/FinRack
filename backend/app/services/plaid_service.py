"""Plaid integration service for bank connections and transactions"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.exceptions import ApiException
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PlaidService:
    """Service for interacting with Plaid API"""
    
    def __init__(self):
        """Initialize Plaid client"""
        configuration = plaid.Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_SECRET,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def _get_plaid_host(self) -> str:
        """Get Plaid API host based on environment"""
        env_hosts = {
            'sandbox': plaid.Environment.Sandbox,
            'development': plaid.Environment.Development,
            'production': plaid.Environment.Production,
        }
        return env_hosts.get(settings.PLAID_ENV, plaid.Environment.Sandbox)
    
    async def create_link_token(
        self,
        user_id: str,
        user_email: str,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a link token for Plaid Link initialization
        
        Args:
            user_id: User ID
            user_email: User email
            redirect_uri: Optional redirect URI for OAuth
            
        Returns:
            Dict with link_token and expiration
        """
        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                client_name=settings.APP_NAME,
                products=[Products("transactions"), Products("auth")],
                country_codes=[CountryCode("US")],
                language='en',
                redirect_uri=redirect_uri,
            )
            
            response = self.client.link_token_create(request)
            
            return {
                'link_token': response['link_token'],
                'expiration': response['expiration'],
            }
        except ApiException as e:
            logger.error(f"Error creating link token: {e}")
            raise Exception(f"Failed to create link token: {str(e)}")
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """
        Exchange public token for access token
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            Dict with access_token and item_id
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            return {
                'access_token': response['access_token'],
                'item_id': response['item_id'],
            }
        except ApiException as e:
            logger.error(f"Error exchanging public token: {e}")
            raise Exception(f"Failed to exchange public token: {str(e)}")
    
    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get accounts for an access token
        
        Args:
            access_token: Plaid access token
            
        Returns:
            List of account dictionaries
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
                    'currency': account['balances']['iso_currency_code'] or 'USD',
                })
            
            return accounts
        except ApiException as e:
            logger.error(f"Error getting accounts: {e}")
            raise Exception(f"Failed to get accounts: {str(e)}")
    
    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for an access token
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions
            end_date: End date for transactions
            account_ids: Optional list of account IDs to filter
            
        Returns:
            List of transaction dictionaries
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                options={
                    'account_ids': account_ids,
                    'count': 500,
                    'offset': 0,
                }
            )
            
            response = self.client.transactions_get(request)
            transactions = []
            
            for txn in response['transactions']:
                transactions.append(self._format_transaction(txn))
            
            # Handle pagination
            total_transactions = response['total_transactions']
            while len(transactions) < total_transactions:
                request.options['offset'] = len(transactions)
                response = self.client.transactions_get(request)
                for txn in response['transactions']:
                    transactions.append(self._format_transaction(txn))
            
            return transactions
        except ApiException as e:
            logger.error(f"Error getting transactions: {e}")
            raise Exception(f"Failed to get transactions: {str(e)}")
    
    async def sync_transactions(
        self,
        access_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync transactions using Plaid's sync endpoint (more efficient)
        
        Args:
            access_token: Plaid access token
            cursor: Optional cursor for pagination
            
        Returns:
            Dict with added, modified, removed transactions and next cursor
        """
        try:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            
            response = self.client.transactions_sync(request)
            
            return {
                'added': [self._format_transaction(txn) for txn in response['added']],
                'modified': [self._format_transaction(txn) for txn in response['modified']],
                'removed': [txn['transaction_id'] for txn in response['removed']],
                'next_cursor': response['next_cursor'],
                'has_more': response['has_more'],
            }
        except ApiException as e:
            logger.error(f"Error syncing transactions: {e}")
            raise Exception(f"Failed to sync transactions: {str(e)}")
    
    def _format_transaction(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """Format Plaid transaction to our schema"""
        location = txn.get('location', {})
        
        return {
            'transaction_id': txn['transaction_id'],
            'account_id': txn['account_id'],
            'amount': float(txn['amount']),
            'date': txn['date'],
            'authorized_date': txn.get('authorized_date'),
            'name': txn['name'],
            'merchant_name': txn.get('merchant_name'),
            'category': txn['category'][0] if txn.get('category') else None,
            'category_detailed': ', '.join(txn['category']) if txn.get('category') else None,
            'payment_channel': txn.get('payment_channel'),
            'location_address': location.get('address'),
            'location_city': location.get('city'),
            'location_region': location.get('region'),
            'location_postal_code': location.get('postal_code'),
            'location_country': location.get('country'),
            'location_lat': location.get('lat'),
            'location_lon': location.get('lon'),
        }
    
    async def handle_webhook(self, webhook_type: str, webhook_code: str, item_id: str) -> Dict[str, Any]:
        """
        Handle Plaid webhooks
        
        Args:
            webhook_type: Type of webhook
            webhook_code: Webhook code
            item_id: Plaid item ID
            
        Returns:
            Dict with action to take
        """
        logger.info(f"Received webhook: {webhook_type} - {webhook_code} for item {item_id}")
        
        actions = {
            'TRANSACTIONS': {
                'INITIAL_UPDATE': {'action': 'sync_transactions', 'priority': 'high'},
                'HISTORICAL_UPDATE': {'action': 'sync_transactions', 'priority': 'medium'},
                'DEFAULT_UPDATE': {'action': 'sync_transactions', 'priority': 'normal'},
                'TRANSACTIONS_REMOVED': {'action': 'remove_transactions', 'priority': 'high'},
            },
            'ITEM': {
                'ERROR': {'action': 'handle_error', 'priority': 'high'},
                'PENDING_EXPIRATION': {'action': 'notify_user', 'priority': 'medium'},
                'USER_PERMISSION_REVOKED': {'action': 'disable_item', 'priority': 'high'},
            },
        }
        
        webhook_actions = actions.get(webhook_type, {})
        return webhook_actions.get(webhook_code, {'action': 'log', 'priority': 'low'})


# Global instance
plaid_service = PlaidService()
