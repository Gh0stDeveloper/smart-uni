"""Migraciones de esquema del backend PostgreSQL. Sin base SQLite."""
from alembic import context
from sqlalchemy import create_engine, pool

from services.api.app.config import Settings
from services.api.app.models import Base

config = context.config
target_metadata = Base.metadata


def run_online():
    cfg = Settings.from_env()
    engine = create_engine(cfg.database_url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                transactional_ddl=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("No generamos migraciones offline sin PostgreSQL real")
run_online()
