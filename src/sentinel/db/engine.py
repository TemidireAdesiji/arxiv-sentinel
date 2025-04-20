"""SQLAlchemy engine factory with connection-pool tuning."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from sentinel.settings import AppSettings

log = structlog.get_logger(__name__)


class DatabaseGateway:
    """Thin wrapper around SQLAlchemy engine + sessionmaker.

    Provides explicit lifecycle methods so the FastAPI lifespan
    can open and close the pool cleanly.
    """

    def __init__(self, dsn: str, *, echo: bool, pool: int, overflow: int):
        self._engine: Engine = create_engine(
            dsn,
            echo=echo,
            pool_size=pool,
            max_overflow=overflow,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    # -- sessions -------------------------------------------------

    def open_session(self) -> Session:
        """Create a new scoped session."""
        return self._session_factory()

    # -- health ---------------------------------------------------

    def verify_connection(self) -> bool:
        """Return *True* if the database is reachable."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            log.warning("db_unreachable")
            return False

    # -- lifecycle ------------------------------------------------

    def dispose(self) -> None:
        """Shut down the connection pool."""
        self._engine.dispose()
        log.info("db_pool_closed")


def create_database_gateway(
    cfg: AppSettings,
) -> DatabaseGateway:
    """Build a ``DatabaseGateway`` from application settings."""
    gw = DatabaseGateway(
        dsn=cfg.db_url,
        echo=cfg.db_echo,
        pool=cfg.db_pool_size,
        overflow=cfg.db_overflow,
    )
    log.info(
        "db_gateway_created",
        pool_size=cfg.db_pool_size,
    )
    return gw
