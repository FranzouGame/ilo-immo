"""historique des prix"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.add_column("property", sa.Column("price_history", postgresql.JSONB(), server_default="[]", nullable=False))


def downgrade() -> None:
    op.drop_column("property", "price_history")
