"""Risk scoring for patrol allocation.

Transparent weighted score per station combining recent volume, heinous-crime
share, and recent trend. Deliberately interpretable (not a black box) so officers
can defend the recommendation. Respects RBAC scope.
"""
from __future__ import annotations

from ..db import query
from ..rbac import User, scope_where


def score(user: User):
    clause, params = scope_where(user, "cm")
    sql = (
        "SELECT u.UnitID, u.UnitName AS Station, d.DistrictName AS District, "
        "COUNT(*) AS TotalCases, "
        "SUM(CASE WHEN g.GravityOffenceName='Heinous' THEN 1 ELSE 0 END) AS Heinous, "
        "SUM(CASE WHEN cm.CrimeRegisteredDate >= date('now','-90 days') THEN 1 ELSE 0 END) AS Recent90, "
        "SUM(CASE WHEN cm.CrimeRegisteredDate >= date('now','-30 days') THEN 1 ELSE 0 END) AS Recent30 "
        "FROM CaseMaster cm "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "JOIN District d ON u.DistrictID = d.DistrictID "
        "JOIN GravityOffence g ON cm.GravityOffenceID = g.GravityOffenceID "
        "WHERE 1=1" + clause +
        " GROUP BY u.UnitID"
    )
    rows = query(sql, tuple(params))
    if not rows:
        return {"answer": "No data to score in your scope.", "scores": [],
                "module": "Risk score"}

    max_recent = max((r["Recent90"] for r in rows), default=1) or 1
    max_total = max((r["TotalCases"] for r in rows), default=1) or 1
    results = []
    for r in rows:
        heinous_share = r["Heinous"] / r["TotalCases"] if r["TotalCases"] else 0
        trend = (r["Recent30"] * 3) - (r["Recent90"] / 3)  # rough acceleration
        risk = (
            0.4 * (r["Recent90"] / max_recent) +
            0.3 * heinous_share +
            0.2 * (r["TotalCases"] / max_total) +
            0.1 * (1 if trend > 0 else 0)
        )
        results.append({
            "Station": r["Station"], "District": r["District"],
            "risk_score": round(risk * 100, 1),
            "total_cases": r["TotalCases"], "heinous": r["Heinous"],
            "recent_90d": r["Recent90"],
            "factors": {
                "recent_volume_weight": 0.4,
                "heinous_share": round(heinous_share, 2),
                "trend_accelerating": trend > 0,
            },
        })
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    answer = (f"Highest patrol-priority station: {results[0]['Station']} "
              f"(risk {results[0]['risk_score']}/100).")
    return {"answer": answer, "scores": results[:15], "module": "Risk score",
            "note": "Risk score is a transparent weighted index of place/time, "
                    "not a prediction about individuals."}
