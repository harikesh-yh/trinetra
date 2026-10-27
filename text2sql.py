"""Text -> SQL module.

Deterministic, offline-first natural-language to SQL over the FIR schema. It is
intentionally NOT a free-form SQL generator: it recognises a bank of crime-analytics
intents and emits *safe, parameterized, read-only* SQL with:

  * a strict table/column whitelist (only SELECTs that we construct),
  * a hard row limit,
  * the RBAC scope WHERE clause injected for the calling user,
  * the exact SQL string returned to the caller ("show the work"),
  * cited CaseMasterIDs so every answer is traceable to source rows.

An optional LLM path (OPENAI_API_KEY) can be added to widen NL coverage; the
deterministic path always runs as a safe fallback.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..db import query
from ..rbac import User, scope_where

ROW_LIMIT = 500

# Crime subhead keyword aliases -> canonical CrimeSubHeadName in the DB.
CRIME_ALIASES = {
    "chain snatch": "Chain Snatching",
    "snatching": "Chain Snatching",
    "vehicle theft": "Vehicle Theft",
    "bike theft": "Vehicle Theft",
    "car theft": "Vehicle Theft",
    "burglary": "House Burglary",
    "house break": "House Burglary",
    "robbery": "Robbery",
    "murder": "Murder",
    "fraud": "Online Financial Fraud",
    "online fraud": "Online Financial Fraud",
    "cheating": "Cheating / Fraud",
    "domestic violence": "Domestic Violence",
    "drug": "Drug Trafficking",
    "narcotic": "Drug Trafficking",
    "pickpocket": "Pickpocketing",
    "kidnap": "Kidnapping",
}

# Relative time windows -> days back from today.
TIME_WINDOWS = {
    "last month": 30,
    "past month": 30,
    "last week": 7,
    "past week": 7,
    "last 3 months": 90,
    "last quarter": 90,
    "last year": 365,
    "this year": 365,
}


@dataclass
class SqlResult:
    answer: str
    sql: str
    params: list
    rows: list
    cited_ids: list[int] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    chart: dict | None = None  # {type, labels, values, title}
    intent: str = "unknown"

    def to_dict(self):
        return {
            "answer": self.answer,
            "sql": _inline_sql(self.sql, self.params),
            "rows": self.rows,
            "columns": self.columns,
            "cited_ids": self.cited_ids,
            "chart": self.chart,
            "intent": self.intent,
            "module": "Text->SQL",
        }


def _inline_sql(sql: str, params: list) -> str:
    """Produce a human-readable SQL string with params inlined (display only)."""
    out = sql
    for p in params:
        rep = f"'{p}'" if isinstance(p, str) else str(p)
        out = out.replace("?", rep, 1)
    return re.sub(r"\s+", " ", out).strip()


def _find_crime(q: str) -> str | None:
    ql = q.lower()
    for alias, canonical in CRIME_ALIASES.items():
        if alias in ql:
            return canonical
    return None


def _find_window_days(q: str) -> int | None:
    ql = q.lower()
    for phrase, days in TIME_WINDOWS.items():
        if phrase in ql:
            return days
    return None


def _cited(rows: list[dict]) -> list[int]:
    ids = []
    for r in rows:
        if "CaseMasterID" in r and r["CaseMasterID"] is not None:
            ids.append(r["CaseMasterID"])
    return ids[:50]


def run(user: User, question: str) -> SqlResult:
    """Map a question to safe SQL, execute it, and return a cited result."""
    q = question.strip()
    ql = q.lower()
    crime = _find_crime(q)
    days = _find_window_days(q)
    scope_clause, scope_params = scope_where(user, "cm")

    # --- Intent: hotspots / top stations for a crime ---
    if any(k in ql for k in ("hotspot", "top station", "which station", "where", "most")):
        where = ["1=1"]
        params: list = []
        if crime:
            where.append("s.CrimeSubHeadName = ?")
            params.append(crime)
        if days:
            where.append("cm.CrimeRegisteredDate >= date('now', ?)")
            params.append(f"-{days} days")
        sql = (
            "SELECT cm.PoliceStationID, u.UnitName AS Station, d.DistrictName AS District, "
            "COUNT(*) AS Cases "
            "FROM CaseMaster cm "
            "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
            "JOIN District d ON u.DistrictID = d.DistrictID "
            "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
            "WHERE " + " AND ".join(where) + scope_clause +
            " GROUP BY cm.PoliceStationID ORDER BY Cases DESC LIMIT 10"
        )
        rows = query(sql, tuple(params + scope_params))
        label = crime or "all crimes"
        win = f" in the {[k for k,v in TIME_WINDOWS.items() if v==days][0]}" if days else ""
        answer = (f"Top stations for {label}{win}: "
                  + ", ".join(f"{r['Station']} ({r['Cases']})" for r in rows[:3])
                  if rows else f"No {label} cases found in your scope{win}.")
        chart = {
            "type": "bar",
            "labels": [r["Station"] for r in rows],
            "values": [r["Cases"] for r in rows],
            "title": f"Cases by station - {label}",
        } if rows else None
        return SqlResult(answer, sql, params + scope_params, rows,
                         columns=["Station", "District", "Cases"], chart=chart,
                         intent="hotspots")

    # --- Intent: count of a crime (optionally in window) ---
    if any(k in ql for k in ("how many", "count", "number of", "total")):
        where = ["1=1"]
        params = []
        if crime:
            where.append("s.CrimeSubHeadName = ?")
            params.append(crime)
        if days:
            where.append("cm.CrimeRegisteredDate >= date('now', ?)")
            params.append(f"-{days} days")
        sql = (
            "SELECT cm.CaseMasterID, cm.CrimeNo, cm.CrimeRegisteredDate, u.UnitName AS Station "
            "FROM CaseMaster cm "
            "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
            "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
            "WHERE " + " AND ".join(where) + scope_clause +
            f" ORDER BY cm.CrimeRegisteredDate DESC LIMIT {ROW_LIMIT}"
        )
        rows = query(sql, tuple(params + scope_params))
        label = crime or "crime"
        answer = f"{len(rows)} {label} case(s) found in your scope" + (
            f" (showing up to {ROW_LIMIT})." if len(rows) >= ROW_LIMIT else ".")
        return SqlResult(answer, sql, params + scope_params, rows,
                         columns=["CaseMasterID", "CrimeNo", "CrimeRegisteredDate", "Station"],
                         cited_ids=_cited(rows), intent="count")

    # --- Intent: monthly trend for a crime ---
    if any(k in ql for k in ("trend", "by month", "over time", "monthly")):
        where = ["1=1"]
        params = []
        if crime:
            where.append("s.CrimeSubHeadName = ?")
            params.append(crime)
        sql = (
            "SELECT substr(cm.CrimeRegisteredDate,1,7) AS Month, COUNT(*) AS Cases "
            "FROM CaseMaster cm "
            "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
            "WHERE " + " AND ".join(where) + scope_clause +
            " GROUP BY Month ORDER BY Month"
        )
        rows = query(sql, tuple(params + scope_params))
        chart = {
            "type": "line",
            "labels": [r["Month"] for r in rows],
            "values": [r["Cases"] for r in rows],
            "title": f"Monthly trend - {crime or 'all crimes'}",
        } if rows else None
        answer = (f"Monthly trend for {crime or 'all crimes'} computed over {len(rows)} months."
                  if rows else "No data for that trend in your scope.")
        return SqlResult(answer, sql, params + scope_params, rows,
                         columns=["Month", "Cases"], chart=chart, intent="trend")

    # --- Intent: recent cases / list ---
    if any(k in ql for k in ("recent", "latest", "list", "show me", "cases")):
        where = ["1=1"]
        params = []
        if crime:
            where.append("s.CrimeSubHeadName = ?")
            params.append(crime)
        if days:
            where.append("cm.CrimeRegisteredDate >= date('now', ?)")
            params.append(f"-{days} days")
        sql = (
            "SELECT cm.CaseMasterID, cm.CrimeNo, cm.CrimeRegisteredDate, "
            "s.CrimeSubHeadName AS Crime, u.UnitName AS Station, cm.BriefFacts "
            "FROM CaseMaster cm "
            "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
            "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
            "WHERE " + " AND ".join(where) + scope_clause +
            " ORDER BY cm.CrimeRegisteredDate DESC LIMIT 25"
        )
        rows = query(sql, tuple(params + scope_params))
        answer = f"{len(rows)} recent case(s) in your scope" + (
            f" for {crime}." if crime else ".")
        return SqlResult(answer, sql, params + scope_params, rows,
                         columns=["CaseMasterID", "CrimeNo", "CrimeRegisteredDate",
                                  "Crime", "Station"],
                         cited_ids=_cited(rows), intent="list")

    # --- Fallback: overall summary in scope ---
    sql = (
        "SELECT s.CrimeSubHeadName AS Crime, COUNT(*) AS Cases "
        "FROM CaseMaster cm "
        "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
        "WHERE 1=1" + scope_clause +
        " GROUP BY s.CrimeSubHeadName ORDER BY Cases DESC LIMIT 10"
    )
    rows = query(sql, tuple(scope_params))
    chart = {
        "type": "bar",
        "labels": [r["Crime"] for r in rows],
        "values": [r["Cases"] for r in rows],
        "title": "Crime mix in your scope",
    } if rows else None
    answer = ("I interpreted that as a request for the crime breakdown in your scope. "
              "Try asking about a specific crime, hotspots, trends, or counts.")
    return SqlResult(answer, sql, scope_params, rows, columns=["Crime", "Cases"],
                     chart=chart, intent="summary")
