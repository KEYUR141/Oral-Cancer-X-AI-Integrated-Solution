import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

DB_URL = (
    f"postgresql://"
    f"{os.environ.get('DB_USER', 'postgres')}:"
    f"{os.environ.get('DB_PASSWORD', '')}@"
    f"{os.environ.get('DB_HOST', 'localhost')}:"
    f"{os.environ.get('DB_PORT', '5432')}/"
    f"{os.environ.get('DB_NAME', 'oral_cancer_rag')}"
)

# create_engine sets up the connection pool — it does NOT open a connection yet.
# pool_pre_ping=True means SQLAlchemy will test the connection before using it,
# so stale connections from the pool don't cause silent failures.
engine = create_engine(DB_URL, pool_pre_ping=True)


@contextmanager
def get_db():
    """
    Context manager that yields a live database connection.
    Automatically commits on success, rolls back on error, and
    always closes the connection when the block exits.

    Usage:
        with get_db() as conn:
            conn.execute(text("SELECT 1"))
    """
    with engine.connect() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


if __name__ == "__main__":
    try:
        with get_db() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info("Engine connected successfully.")
            logger.info(f"PostgreSQL: {version}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")
