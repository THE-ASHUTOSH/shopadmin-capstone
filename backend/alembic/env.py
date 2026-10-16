from logging.config import fileConfig

from alembic import context
from sqlalchemy import text

from app import models  # noqa: F401
from app.db import Base, engine

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

with engine.connect() as conn:
    # several backend pods start together, only one should migrate at a time
    if conn.dialect.name == "postgresql":
        conn.execute(text("select pg_advisory_lock(42)"))
        conn.commit()
    context.configure(connection=conn, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
