import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signalx.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_signals (
            guid TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_sent(guid: str) -> bool:
    """Check if a signal GUID has already been sent."""
    conn = _get_conn()
    row = conn.execute("SELECT 1 FROM sent_signals WHERE guid = ?", (guid,)).fetchone()
    conn.close()
    return row is not None


def mark_sent(guid: str):
    """Record a signal GUID as sent."""
    conn = _get_conn()
    conn.execute("INSERT OR IGNORE INTO sent_signals (guid) VALUES (?)", (guid,))
    conn.commit()
    conn.close()
