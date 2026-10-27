"""Anomaly watch: spike detection per crime-type x station x month using a
rolling z-score. Flags months whose case count exceeds mean + k*std of the
station/crime's own history. Respects RBAC scope.
"""
from __future__ import annotations

import statistics

from ..db import query
from ..rbac import User, scope_where


def detect(user: User, z_threshold: float = 2.0):
    clause, params = scope_where(user, "cm")
    sql = (
        "SELECT u.UnitName AS Station, s.CrimeSubHeadName AS Crime, "
        "substr(cm.CrimeRegisteredDate,1,7) AS Month, COUNT(*) AS Cases "
        "FROM CaseMaster cm "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
        "WHERE 1=1" + clause +
        " GROUP BY Station, Crime, Month ORDER BY Station, Crime, Month"
    )
    rows = query(sql, tuple(params))

    series: dict[tuple, list[tuple]] = {}
    for r in rows:
        series.setdefault((r["Station"], r["Crime"]), []).append((r["Month"], r["Cases"]))

    alerts = []
    for (station, crime), pts in series.items():
        counts = [c for _, c in pts]
        if len(counts) < 4:
            continue
        mean = statistics.mean(counts)
        std = statistics.pstdev(counts)
        if std == 0:
            continue
        for month, c in pts:
            z = (c - mean) / std
            # Require a meaningful absolute count so tiny series (1->2) don't spam.
            if z >= z_threshold and c > mean and c >= 5:
                alerts.append({
                    "Station": station, "Crime": crime, "Month": month,
                    "Cases": c, "baseline_mean": round(mean, 1),
                    "z_score": round(z, 2),
                    "severity": "high" if z >= 3 else "medium",
                })
    alerts.sort(key=lambda a: a["z_score"], reverse=True)
    answer = (f"{len(alerts)} anomaly alert(s) detected. Top: {alerts[0]['Crime']} spike "
              f"at {alerts[0]['Station']} in {alerts[0]['Month']} "
              f"({alerts[0]['Cases']} vs baseline {alerts[0]['baseline_mean']})."
              if alerts else "No significant anomalies detected in your scope.")
    return {"answer": answer, "alerts": alerts[:25], "module": "Anomaly watch"}
