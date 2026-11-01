from sqlalchemy import create_engine

from alembic import context
from app.config import db_url, settings
from app.models import Base

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    """Ignore tout ce qui n'est pas dans nos modèles (tables tiger/topology de l'image PostGIS)."""
    if type_ == "table":
        return name in target_metadata.tables
    table = getattr(obj, "table", None)
    return table is None or table.name in target_metadata.tables


def run() -> None:
    engine = create_engine(db_url(settings()))
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


run()
