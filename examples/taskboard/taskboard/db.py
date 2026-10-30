# SPDX-License-Identifier: Apache-2.0
"""SQLite schema creation and a tiny forward-only migration list."""
import sqlite3

# (version, SQL). Append new entries; never edit one that has shipped.
MIGRATIONS = [
    (1, """CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT NOT NULL,
        title TEXT NOT NULL,
        due TEXT,
        done INTEGER NOT NULL DEFAULT 0
    )"""),
]


def current_version(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def migrate(conn):
    """Apply every migration newer than the database's version. Safe to call repeatedly."""
    applied = current_version(conn)
    for version, sql in MIGRATIONS:
        if version > applied:
            conn.execute(sql)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    migrate(conn)
    return conn
