"""Hotspot detection + lightweight next-period forecast.

Aggregates cases by station (with lat/long) for the map, and produces a simple
forecast for the next month using a 3-month moving average + linear trend. No
heavy time-series dependency; transparent and explainable.
Respects RBAC scope.
"""
from __future__ import annotations

from ..db import query
from ..rbac import User, scope_where


def hotspots(user: User, crime: str | None = None, days: int | None = 90):
    clause, params = scope_where(user, "cm")
    where = ["cm.Latitude IS NOT NULL"]
    p = []
    if crime:
        where.append("s.CrimeSubHeadName = ?")
        p.append(crime)
    if days:
        where.append("cm.CrimeRegisteredDate >= date('now', ?)")
        p.append(f"-{days} days")
    sql = (
        "SELECT u.UnitID, u.UnitName AS Station, d.DistrictName AS District, "
        "u.Latitude AS lat, u.Longitude AS lng, COUNT(*) AS Cases "
        "FROM CaseMaster cm "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "JOIN District d ON u.DistrictID = d.DistrictID "
        "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
        "WHERE " + " AND ".join(where) + clause +
        " GROUP BY u.UnitID ORDER BY Cases DESC"
    )
    rows = query(sql, tuple(p + params))
    return {
        "points": rows,
        "crime": crime or "all crimes",
        "module": "Hotspot",
        "max_cases": max((r["Cases"] for r in rows), default=0),
    }


def forecast(user: User, crime: str | None = None):
    """Next-month forecast per station using moving average + linear trend."""
    clause, params = scope_where(user, "cm")
    where = ["1=1"]
    p = []
    if crime:
        where.append("s.CrimeSubHeadName = ?")
        p.append(crime)
    sql = (
        "SELECT u.UnitName AS Station, substr(cm.CrimeRegisteredDate,1,7) AS Month, "
        "COUNT(*) AS Cases "
        "FROM CaseMaster cm "
        "JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "JOIN CrimeSubHead s ON cm.CrimeMinorHeadID = s.CrimeMinorHeadID "
        "WHERE " + " AND ".join(where) + clause +
        " GROUP BY u.UnitName, Month ORDER BY u.UnitName, Month"
    )
    rows = query(sql, tuple(p + params))
    by_station: dict[str, list[int]] = {}
    for r in rows:
        by_station.setdefault(r["Station"], []).append(r["Cases"])

    forecasts = []
    for station, series in by_station.items():
        if len(series) < 2:
            pred = series[-1] if series else 0
        else:
            window = series[-3:]
            ma = sum(window) / len(window)
            trend = series[-1] - series[-2]
            pred = max(0, round(ma + 0.5 * trend))
        forecasts.append({
            "Station": station,
            "recent": series[-3:],
            "forecast_next_month": pred,
        })
    forecasts.sort(key=lambda x: x["forecast_next_month"], reverse=True)
    top = forecasts[0] if forecasts else None
    answer = (f"Highest predicted {crime or 'crime'} next month: {top['Station']} "
              f"(~{top['forecast_next_month']} cases). Recommend increased patrol allocation."
              if top else "Insufficient data to forecast in your scope.")
    return {"answer": answer, "forecasts": forecasts[:10], "module": "Forecast"}
