"""suivi de disparition des annonces"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.add_column("property", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("property", sa.Column("gone", sa.Boolean(), server_default="false", nullable=False))


def downgrade() -> None:
    op.drop_column("property", "gone")
    op.drop_column("property", "last_seen_at")
