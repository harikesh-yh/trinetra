"""Response-lag analytics: gaps between incident, info-received, and registration.

Long lags can indicate underreporting or delayed registration. Computes average
lag (days) per station and flags outliers. Respects RBAC scope.
"""
from __future__ import annotations

from ..db import query
from ..rbac import User, scope_where


def by_station(user: User, min_cases: int = 15):
    clause, params = scope_where(user, "cm")
    sql = (
        "SELECT u.UnitName AS Station, "
        "COUNT(*) AS Cases, "
        "AVG(julianday(cm.CrimeRegisteredDate) - julianday(cm.IncidentFromDate)) AS AvgLagDays, "
        "MAX(julianday(cm.CrimeRegisteredDate) - julianday(cm.IncidentFromDate)) AS MaxLagDays "
        "FROM CaseMaster cm "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "WHERE cm.IncidentFromDate IS NOT NULL" + clause +
        " GROUP BY u.UnitID HAVING Cases >= ?"
    )
    rows = query(sql, tuple(params + [min_cases]))
    results = [{
        "Station": r["Station"], "cases": r["Cases"],
        "avg_lag_days": round(r["AvgLagDays"] or 0, 1),
        "max_lag_days": round(r["MaxLagDays"] or 0, 1),
    } for r in rows]
    results.sort(key=lambda x: x["avg_lag_days"], reverse=True)
    answer = (f"Highest average registration lag: {results[0]['Station']} "
              f"({results[0]['avg_lag_days']} days). May indicate delayed reporting/registration."
              if results else "Not enough data to compute response lag in your scope.")
    return {"answer": answer, "stations": results, "module": "Response lag"}
