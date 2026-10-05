import logging
from collections.abc import Generator

from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

try:
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.core.config import settings

logger = logging.getLogger(__name__)

# Connect args (fast failover timeout if DB is unreachable)
connect_args = {}
if "postgresql" in settings.SQLALCHEMY_DATABASE_URI:
    connect_args["connect_timeout"] = 3

# Engine configuration for PostgreSQL / SQLAlchemy
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(target: Engine | Connection | None = None) -> bool:
    """Check if the database is reachable and accepts queries."""
    target_obj = target or engine
    try:
        if hasattr(target_obj, "connect"):
            with target_obj.connect() as connection:
                connection.execute(text("SELECT 1"))
        else:
            target_obj.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Unexpected error during database connection check: %s", exc)
        return False
