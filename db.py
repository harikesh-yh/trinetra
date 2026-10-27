"""SQLite connection helpers for the TRINETRA engine."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TRINETRA_DB", os.path.join(HERE, "..", "trinetra.db"))
DB_PATH = os.path.abspath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


@contextmanager
def cursor():
    con = get_connection()
    try:
        yield con.cursor()
        con.commit()
    finally:
        con.close()


def query(sql: str, params: tuple = ()):  # read helper
    con = get_connection()
    try:
        rows = con.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def db_exists() -> bool:
    return os.path.exists(DB_PATH)
