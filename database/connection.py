"""
ZeroGraph AI — SQLite Connection Manager
Thread-safe connection management with WAL mode for concurrent reads.
"""

import os
import sqlite3
import threading

from config import Config


_local = threading.local()


def get_connection(db_path=None):
    """Get a thread-local SQLite connection with optimized pragmas."""
    path = db_path or Config.ZEROGRAPH_DB_PATH
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)

    if not hasattr(_local, "connections"):
        _local.connections = {}

    if path not in _local.connections or _local.connections[path] is None:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        _local.connections[path] = conn

    return _local.connections[path]


def get_legacy_connection():
    """Get connection to the original knowledge_graph.db for migration."""
    return get_connection(Config.SQLITE_DB_PATH)


def close_all():
    """Close all thread-local connections."""
    if hasattr(_local, "connections"):
        for conn in _local.connections.values():
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        _local.connections = {}


def dict_from_row(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows):
    """Convert a list of sqlite3.Row to a list of dicts."""
    return [dict(row) for row in rows]
