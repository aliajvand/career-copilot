"""Initial enterprise migration: composite indexes, soft deletes, audit_logs and transactions

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-30 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('changes_json', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action', 'created_at'])

    # Transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('authority', sa.String(length=100), unique=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending'),
        sa.Column('gateway', sa.String(length=50), server_default='zarinpal_sandbox'),
        sa.Column('ref_id', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=100), unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('verified_at', sa.DateTime(), nullable=True)
    )
    op.create_index('idx_transactions_user', 'transactions', ['user_id', 'status'])

def downgrade():
    op.drop_table('transactions')
    op.drop_table('audit_logs')
