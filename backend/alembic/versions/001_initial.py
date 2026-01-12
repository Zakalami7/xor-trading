"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(100)),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('mfa_enabled', sa.Boolean(), default=False, nullable=False),
        sa.Column('mfa_secret_encrypted', sa.Text()),
        sa.Column('mfa_backup_codes', sa.JSON()),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('last_login_ip', sa.String(45)),
        sa.Column('risk_settings', sa.JSON(), default={}),
        sa.Column('settings', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.func.now()),
    )
    
    # API Credentials table
    op.create_table(
        'api_credentials',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('passphrase_encrypted', sa.Text()),
        sa.Column('api_key_last4', sa.String(4)),
        sa.Column('is_testnet', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('permissions', sa.JSON(), default={}),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    
    # Strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('config_schema', sa.JSON()),
        sa.Column('default_params', sa.JSON(), default={}),
        sa.Column('supported_markets', sa.JSON()),
        sa.Column('risk_level', sa.String(20)),
        sa.Column('indicators', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Bots table
    op.create_table(
        'bots',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('api_credential_id', sa.Uuid(), sa.ForeignKey('api_credentials.id')),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('base_asset', sa.String(10), nullable=False),
        sa.Column('quote_asset', sa.String(10), nullable=False),
        sa.Column('market_type', sa.String(20), default='spot'),
        sa.Column('strategy_id', sa.Uuid(), sa.ForeignKey('strategies.id')),
        sa.Column('strategy_params', sa.JSON(), default={}),
        sa.Column('status', sa.String(20), default='created'),
        sa.Column('status_message', sa.Text()),
        sa.Column('position_size', sa.Float),
        sa.Column('position_size_type', sa.String(20), default='fixed'),
        sa.Column('max_positions', sa.Integer(), default=1),
        sa.Column('leverage', sa.Integer(), default=1),
        sa.Column('margin_type', sa.String(20)),
        sa.Column('max_drawdown_percent', sa.Float),
        sa.Column('stop_loss_percent', sa.Float),
        sa.Column('take_profit_percent', sa.Float),
        sa.Column('trailing_stop_percent', sa.Float),
        sa.Column('total_trades', sa.Integer(), default=0),
        sa.Column('winning_trades', sa.Integer(), default=0),
        sa.Column('losing_trades', sa.Integer(), default=0),
        sa.Column('total_pnl', sa.Float, default=0),
        sa.Column('total_pnl_percent', sa.Float, default=0),
        sa.Column('max_drawdown_reached', sa.Float, default=0),
        sa.Column('total_fees', sa.Float, default=0),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('stopped_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    
    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('bot_id', sa.Uuid(), sa.ForeignKey('bots.id')),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('exchange_order_id', sa.String(100)),
        sa.Column('client_order_id', sa.String(100), unique=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('order_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('filled_quantity', sa.Float, default=0),
        sa.Column('price', sa.Float),
        sa.Column('average_price', sa.Float),
        sa.Column('stop_price', sa.Float),
        sa.Column('fee', sa.Float, default=0),
        sa.Column('fee_asset', sa.String(10)),
        sa.Column('reduce_only', sa.Boolean(), default=False),
        sa.Column('post_only', sa.Boolean(), default=False),
        sa.Column('time_in_force', sa.String(10), default='GTC'),
        sa.Column('latency_ms', sa.Integer()),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('filled_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('bot_id', sa.Uuid(), sa.ForeignKey('bots.id')),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('entry_price', sa.Float, nullable=False),
        sa.Column('current_price', sa.Float),
        sa.Column('exit_price', sa.Float),
        sa.Column('leverage', sa.Integer(), default=1),
        sa.Column('liquidation_price', sa.Float),
        sa.Column('unrealized_pnl', sa.Float, default=0),
        sa.Column('realized_pnl', sa.Float, default=0),
        sa.Column('total_fees', sa.Float, default=0),
        sa.Column('stop_loss_price', sa.Float),
        sa.Column('take_profit_price', sa.Float),
        sa.Column('trailing_stop_distance', sa.Float),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('bot_id', sa.Uuid(), sa.ForeignKey('bots.id')),
        sa.Column('order_id', sa.Uuid(), sa.ForeignKey('orders.id')),
        sa.Column('position_id', sa.Uuid(), sa.ForeignKey('positions.id')),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('exchange_trade_id', sa.String(100)),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('fee', sa.Float, default=0),
        sa.Column('fee_asset', sa.String(10)),
        sa.Column('realized_pnl', sa.Float),
        sa.Column('is_maker', sa.Boolean(), default=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('details', sa.JSON()),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Indexes
    op.create_index('ix_bots_user_status', 'bots', ['user_id', 'status'])
    op.create_index('ix_orders_user_created', 'orders', ['user_id', 'created_at'])
    op.create_index('ix_positions_user_status', 'positions', ['user_id', 'status'])
    op.create_index('ix_trades_user_executed', 'trades', ['user_id', 'executed_at'])
    op.create_index('ix_audit_user_created', 'audit_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('trades')
    op.drop_table('positions')
    op.drop_table('orders')
    op.drop_table('bots')
    op.drop_table('strategies')
    op.drop_table('api_credentials')
    op.drop_table('users')
