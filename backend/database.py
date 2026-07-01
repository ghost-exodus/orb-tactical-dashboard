import sqlite3
from contextlib import contextmanager
from typing import Generator

DATABASE_URL = "orb_logs.db"


def init_db():
    """Initialize the SQLite database with the alerts table."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Create alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            alert_time DATETIME NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('BULLISH', 'BEARISH')),
            breakout_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target REAL NOT NULL,
            range_high REAL NOT NULL,
            range_low REAL NOT NULL,
            status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'TRADED', 'SKIPPED')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_time ON alerts(alert_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON alerts(status)")

    conn.commit()
    conn.close()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # To access columns by name
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a SELECT query and return results."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount