"""Initial schema with all models

Revision ID: 001
Revises: 
Create Date: 2025-01-03 01:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False),
        sa.Column('mfa_secret', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create profiles table
    op.create_table('profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('profile_picture_url', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('date_format', sa.String(length=20), nullable=False),
        sa.Column('number_format', sa.String(length=20), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=False),
        sa.Column('preferred_llm_provider', sa.String(length=50), nullable=False),
        sa.Column('notification_preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('large_transaction_threshold', sa.String(length=20), nullable=False),
        sa.Column('budget_warning_percentage', sa.String(length=10), nullable=False),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create bank_accounts table
    op.create_table('bank_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plaid_account_id', sa.String(length=255), nullable=False),
        sa.Column('plaid_access_token', sa.String(length=255), nullable=False),
        sa.Column('plaid_item_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('official_name', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('account_subtype', sa.String(length=50), nullable=True),
        sa.Column('mask', sa.String(length=10), nullable=True),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('available_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('limit_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('institution_id', sa.String(length=255), nullable=True),
        sa.Column('institution_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_manual', sa.Boolean(), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False),
        sa.Column('sync_error', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plaid_account', 'bank_accounts', ['plaid_account_id'], unique=False)
    op.create_index('idx_user_accounts', 'bank_accounts', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_bank_accounts_plaid_account_id'), 'bank_accounts', ['plaid_account_id'], unique=True)
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plaid_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('authorized_date', sa.Date(), nullable=True),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('original_description', sa.Text(), nullable=True),
        sa.Column('merchant_name', sa.String(length=255), nullable=True),
        sa.Column('merchant_entity_id', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('category_detailed', sa.String(length=255), nullable=True),
        sa.Column('category_confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('location_address', sa.String(length=500), nullable=True),
        sa.Column('location_city', sa.String(length=100), nullable=True),
        sa.Column('location_region', sa.String(length=100), nullable=True),
        sa.Column('location_postal_code', sa.String(length=20), nullable=True),
        sa.Column('location_country', sa.String(length=2), nullable=True),
        sa.Column('location_lat', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('location_lon', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('payment_channel', sa.String(length=50), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('is_pending', sa.Boolean(), nullable=False),
        sa.Column('user_category', sa.String(length=100), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('is_hidden', sa.Boolean(), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=False),
        sa.Column('receipt_url', sa.Text(), nullable=True),
        sa.Column('has_receipt', sa.Boolean(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('fraud_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False),
        sa.Column('fraud_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transaction_account_date', 'transactions', ['account_id', 'date'], unique=False)
    op.create_index('idx_transaction_amount', 'transactions', ['amount'], unique=False)
    op.create_index('idx_transaction_category', 'transactions', ['category'], unique=False)
    op.create_index('idx_transaction_date', 'transactions', ['date'], unique=False)
    op.create_index('idx_transaction_merchant', 'transactions', ['merchant_name'], unique=False)
    op.create_index(op.f('ix_transactions_plaid_transaction_id'), 'transactions', ['plaid_transaction_id'], unique=True)
    
    # Create vector index for transactions
    op.execute('CREATE INDEX idx_transaction_embedding ON transactions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')
    
    # Convert transactions to hypertable for TimescaleDB
    op.execute("SELECT create_hypertable('transactions', 'date', if_not_exists => TRUE)")
    
    # Create budgets table
    op.create_table('budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('current_spent', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('remaining', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('percentage_used', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('rollover_unused', sa.Boolean(), nullable=False),
        sa.Column('alert_enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_threshold', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_calculated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_budget_period', 'budgets', ['start_date', 'end_date'], unique=False)
    op.create_index('idx_budget_user_category', 'budgets', ['user_id', 'category'], unique=False)
    op.create_index(op.f('ix_budgets_category'), 'budgets', ['category'], unique=False)
    
    # Create budget_alerts table
    op.create_table('budget_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('budget_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('threshold', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('is_triggered', sa.Boolean(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_budget', 'budget_alerts', ['budget_id', 'is_triggered'], unique=False)
    
    # Create financial_goals table
    op.create_table('financial_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('percentage_complete', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('required_monthly_savings', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('projected_completion_date', sa.Date(), nullable=True),
        sa.Column('probability_of_success', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('linked_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('achieved_at', sa.DateTime(), nullable=True),
        sa.Column('last_calculated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['linked_account_id'], ['bank_accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_goal_deadline', 'financial_goals', ['deadline'], unique=False)
    op.create_index('idx_goal_user_status', 'financial_goals', ['user_id', 'status'], unique=False)
    
    # Create goal_progress table
    op.create_table('goal_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('entry_type', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['financial_goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_progress_goal_date', 'goal_progress', ['goal_id', 'date'], unique=False)
    
    # Create agent_tasks table
    op.create_table('agent_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.String(length=20), nullable=True),
        sa.Column('tokens_used', sa.String(length=20), nullable=True),
        sa.Column('cost', sa.String(length=20), nullable=True),
        sa.Column('llm_provider', sa.String(length=50), nullable=True),
        sa.Column('llm_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_task_status', 'agent_tasks', ['status', 'created_at'], unique=False)
    op.create_index('idx_agent_task_user_agent', 'agent_tasks', ['user_id', 'agent_name'], unique=False)
    op.create_index(op.f('ix_agent_tasks_agent_name'), 'agent_tasks', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_tasks_created_at'), 'agent_tasks', ['created_at'], unique=False)
    
    # Create agent_memory table
    op.create_table('agent_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('importance_score', sa.String(length=10), nullable=True),
        sa.Column('access_count', sa.String(length=20), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_memory_agent_type', 'agent_memory', ['agent_name', 'memory_type'], unique=False)
    op.create_index('idx_memory_user', 'agent_memory', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_agent_memory_agent_name'), 'agent_memory', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_memory_created_at'), 'agent_memory', ['created_at'], unique=False)
    
    # Create vector index for agent_memory
    op.execute('CREATE INDEX idx_memory_embedding ON agent_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_agent_memory_created_at'), table_name='agent_memory')
    op.drop_index(op.f('ix_agent_memory_agent_name'), table_name='agent_memory')
    op.drop_index('idx_memory_user', table_name='agent_memory')
    op.drop_index('idx_memory_agent_type', table_name='agent_memory')
    op.drop_table('agent_memory')
    
    op.drop_index(op.f('ix_agent_tasks_created_at'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_agent_name'), table_name='agent_tasks')
    op.drop_index('idx_agent_task_user_agent', table_name='agent_tasks')
    op.drop_index('idx_agent_task_status', table_name='agent_tasks')
    op.drop_table('agent_tasks')
    
    op.drop_index('idx_progress_goal_date', table_name='goal_progress')
    op.drop_table('goal_progress')
    
    op.drop_index('idx_goal_user_status', table_name='financial_goals')
    op.drop_index('idx_goal_deadline', table_name='financial_goals')
    op.drop_table('financial_goals')
    
    op.drop_index('idx_alert_budget', table_name='budget_alerts')
    op.drop_table('budget_alerts')
    
    op.drop_index(op.f('ix_budgets_category'), table_name='budgets')
    op.drop_index('idx_budget_user_category', table_name='budgets')
    op.drop_index('idx_budget_period', table_name='budgets')
    op.drop_table('budgets')
    
    op.drop_index(op.f('ix_transactions_plaid_transaction_id'), table_name='transactions')
    op.drop_index('idx_transaction_merchant', table_name='transactions')
    op.drop_index('idx_transaction_date', table_name='transactions')
    op.drop_index('idx_transaction_category', table_name='transactions')
    op.drop_index('idx_transaction_amount', table_name='transactions')
    op.drop_index('idx_transaction_account_date', table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index(op.f('ix_bank_accounts_plaid_account_id'), table_name='bank_accounts')
    op.drop_index('idx_user_accounts', table_name='bank_accounts')
    op.drop_index('idx_plaid_account', table_name='bank_accounts')
    op.drop_table('bank_accounts')
    
    op.drop_table('profiles')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    op.execute('DROP EXTENSION IF EXISTS postgis')
    op.execute('DROP EXTENSION IF EXISTS timescaledb')
    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
