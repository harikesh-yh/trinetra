"""Socio-economic correlation (GUARDRAILED).

Aggregates complainant/victim demographics (occupation, age band, gender) for a
crime type to surface VICTIMIZATION patterns for resource targeting - never
predictive profiling of individuals or groups. A bias disclaimer is always
attached. Caste/religion dimensions are summarized only at aggregate level with
an explicit warning. Respects RBAC scope.
"""
from __future__ import annotations

from ..db import query
from ..rbac import User, scope_where

DISCLAIMER = (
    "Demographic data is presented as VICTIMIZATION and resource-targeting insight "
    "only. It must NOT be used to profile or predict criminality of any individual "
    "or community. Correlation is not causation; sample sizes vary."
)


def victimization(user: User, crime: str | None = None, dimension: str = "occupation"):
    clause, params = scope_where(user, "cm")
    dim_sql = {
        "occupation": ("o.OccupationName", "OccupationMaster o ON c.OccupationID = o.OccupationID"),
        "gender": ("g.GenderName", "GenderMaster g ON c.GenderID = g.GenderID"),
        "religion": ("r.ReligionName", "ReligionMaster r ON c.ReligionID = r.ReligionID"),
        "caste": ("ca.CasteName", "CasteMaster ca ON c.CasteID = ca.CasteID"),
    }
    if dimension not in dim_sql:
        dimension = "occupation"
    col, join = dim_sql[dimension]
    where = ["1=1"]
    p = []
    if crime:
        where.append("s.CrimeSubHeadName = ?")
        p.append(crime)
    sql = (
        f"SELECT {col} AS Category, COUNT(*) AS Cases "
        "FROM ComplainantDetails c "
        "JOIN CaseMaster cm ON c.CaseMasterID = cm.CaseMasterID "
        "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
        f"JOIN {join} "
        "WHERE " + " AND ".join(where) + clause +
        " GROUP BY Category ORDER BY Cases DESC"
    )
    rows = query(sql, tuple(p + params))
    total = sum(r["Cases"] for r in rows)
    results = [{"Category": r["Category"], "Cases": r["Cases"],
                "share_pct": round(100 * r["Cases"] / total, 1) if total else 0}
               for r in rows]
    answer = (f"Victimization by {dimension} for {crime or 'all crimes'}: top group "
              f"is {results[0]['Category']} ({results[0]['share_pct']}%)."
              if results else "No demographic data in your scope.")
    return {
        "answer": answer,
        "dimension": dimension,
        "crime": crime or "all crimes",
        "breakdown": results,
        "chart": {"type": "bar", "labels": [r["Category"] for r in results],
                  "values": [r["Cases"] for r in results],
                  "title": f"Victimization by {dimension} - {crime or 'all crimes'}"},
        "bias_disclaimer": DISCLAIMER,
        "sensitive": dimension in ("religion", "caste"),
        "module": "Socio-economic",
    }
