"""initial database schema

Revision ID: 043b55cb56e3
Revises: 
Create Date: 2026-07-09 19:05:24.160282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '043b55cb56e3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "deutsche_bank_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_name", sa.String(length=150), nullable=False),
        sa.Column("annual_fee", sa.Float(), nullable=True),
        sa.Column("reward_type", sa.String(length=100), nullable=True),
        sa.Column("lounge_access", sa.Boolean(), nullable=True),
        sa.Column("forex_markup", sa.Float(), nullable=True),
        sa.Column("best_for", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deutsche_bank_cards_id"), "deutsche_bank_cards", ["id"], unique=False)
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("merchant", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("card_used", sa.String(length=150), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    op.create_table(
        "reward_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("reward_percent", sa.Float(), nullable=True),
        sa.Column("monthly_cap", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["deutsche_bank_cards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reward_rules_id"), "reward_rules", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_reward_rules_id"), table_name="reward_rules")
    op.drop_table("reward_rules")
    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_deutsche_bank_cards_id"), table_name="deutsche_bank_cards")
    op.drop_table("deutsche_bank_cards")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
