"""Simple database migrations for the current MVP."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from minebridge_frp.app.db.database import Base


def run_migrations(engine: Engine) -> None:
    """Create missing tables.

    Stage 2 intentionally uses SQLAlchemy's metadata creation. A future release can
    replace this with Alembic once schema migrations become more complex.
    """
    Base.metadata.create_all(engine)
