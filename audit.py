"""Audit log: every engine query is recorded (who / role / scope / question / SQL)."""
from __future__ import annotations

from datetime import datetime

from .db import cursor, query
from .rbac import User


def log(user: User, question: str, module: str, sql_run: str = ""):
    with cursor() as cur:
        cur.execute(
            """INSERT INTO AuditLog (Username, Role, Scope, Question, Module, SQLRun, Timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user.username, user.role, user.scope_label, question, module,
             sql_run, datetime.now().isoformat(timespec="seconds")),
        )


def recent(limit: int = 50):
    return query(
        "SELECT * FROM AuditLog ORDER BY AuditID DESC LIMIT ?", (limit,)
    )
