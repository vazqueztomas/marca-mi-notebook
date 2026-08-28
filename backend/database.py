from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from config import get_settings

settings = get_settings()


# Supabase Postgres DSN: postgresql://postgres:password@host/database
def get_db_url() -> str:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set — configure it in .env / Vercel env")
    return settings.database_url


@contextmanager
def get_connection():
    """Get DB connection with transaction support."""
    conn = psycopg2.connect(get_db_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params=None, fetch_one=False):
    """Execute query and return results."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch_one:
                return cur.fetchone()
            return cur.fetchall()


def execute_update(query: str, params=None) -> int:
    """Execute update and return affected rows."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


@contextmanager
def get_transaction():
    """Get transaction context with FOR UPDATE support for row locking."""
    conn = psycopg2.connect(get_db_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create schema on startup."""
    from loguru import logger

    migrations_dir = Path(__file__).parent / "migrations"
    schema_file = migrations_dir / "001_initial_schema.sql"
    with open(schema_file) as f:
        schema = f.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
    logger.info("Database schema initialized")


def seed_db():
    """Seed initial data (spots)."""
    from loguru import logger

    migrations_dir = Path(__file__).parent / "migrations"
    seed_file = migrations_dir / "002_seed_spots.sql"
    with open(seed_file) as f:
        seed = f.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(seed)
    logger.info("Database seeded with initial spots")
