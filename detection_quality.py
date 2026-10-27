"""Detection-quality analytics from ChargesheetDetails.cstype.

  A = Chargesheet (detected), B = False Case, C = Undetected.

Computes per-station chargesheet / false-case / undetected rates. High false-case
or undetected rates flag stations that may need review. Respects RBAC scope.
"""
from __future__ import annotations

from ..db import query
from ..rbac import User, scope_where


def by_station(user: User, min_cases: int = 15):
    clause, params = scope_where(user, "cm")
    sql = (
        "SELECT u.UnitName AS Station, d.DistrictName AS District, "
        "COUNT(*) AS Total, "
        "SUM(ch.cstype='A') AS Chargesheeted, "
        "SUM(ch.cstype='B') AS FalseCase, "
        "SUM(ch.cstype='C') AS Undetected "
        "FROM ChargesheetDetails ch "
        "JOIN CaseMaster cm ON ch.CaseMasterID = cm.CaseMasterID "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "JOIN District d ON u.DistrictID = d.DistrictID "
        "WHERE 1=1" + clause +
        " GROUP BY u.UnitID HAVING Total >= ?"
    )
    rows = query(sql, tuple(params + [min_cases]))
    results = []
    for r in rows:
        t = r["Total"]
        results.append({
            "Station": r["Station"], "District": r["District"], "total": t,
            "chargesheet_rate": round(100 * r["Chargesheeted"] / t, 1),
            "false_case_rate": round(100 * r["FalseCase"] / t, 1),
            "undetected_rate": round(100 * r["Undetected"] / t, 1),
        })
    results.sort(key=lambda x: x["false_case_rate"], reverse=True)
    answer = (f"Station with highest false-case rate: {results[0]['Station']} "
              f"({results[0]['false_case_rate']}% of {results[0]['total']} cases). "
              f"Recommend supervisory review."
              if results else "Not enough chargesheet data in your scope.")
    return {"answer": answer, "stations": results, "module": "Detection quality",
            "legend": {"A": "Chargesheet", "B": "False Case", "C": "Undetected"}}
