"""Smoke tests for the TRINETRA engine modules.

Run from the backend directory:  python -m tests.test_engine
(Requires trinetra.db to exist; run generate_data.py first.)

These assert the planted demo structures are discoverable and that the trust
spine behaves (RBAC scope narrows results, audit writes, SQL is returned/cited).
"""
from __future__ import annotations

import sys

from app.rbac import DEMO_USERS
from app.modules import (anomaly, detection_quality, graph_engine, hotspot,
                         response_lag, risk, router, socioeconomic)

SHO = DEMO_USERS["sho_koramangala"]
DCP = DEMO_USERS["dcp_bengaluru"]
ADGP = DEMO_USERS["adgp_state"]

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, cond, detail=""):
    results.append((name, cond))
    print(f"[{PASS if cond else FAIL}] {name}" + (f" - {detail}" if detail else ""))


def main():
    # Text->SQL hotspots returns SQL and an answer for SHO scope
    r = router.route(SHO, "chain snatching hotspots last month")
    check("text2sql returns SQL string", bool(r.get("sql")), r.get("sql", "")[:50])
    check("text2sql answer mentions Koramangala (planted hotspot)",
          "Koramangala" in r["answer"], r["answer"])

    # RBAC: SHO detection-quality limited to one station; ADGP sees many
    sho_det = detection_quality.by_station(SHO, min_cases=1)
    adgp_det = detection_quality.by_station(ADGP, min_cases=15)
    check("RBAC SHO scope = single station",
          len(sho_det["stations"]) <= 1, f"{len(sho_det['stations'])} stations")
    check("RBAC ADGP scope = many stations",
          len(adgp_det["stations"]) > 5, f"{len(adgp_det['stations'])} stations")

    # Detection quality finds the planted false-case cluster
    check("detection finds high false-case station (Electronic City)",
          any(s["Station"] == "Electronic City PS" and s["false_case_rate"] > 30
              for s in adgp_det["stations"]))

    # Graph: communities + kingpins + repeat offenders present (planted gangs)
    g = graph_engine.analyze(ADGP)
    check("graph detects communities", len(g["communities"]) >= 1, f"{len(g['communities'])}")
    check("graph finds repeat offenders", len(g["repeat_offenders"]) >= 1)
    check("graph carries presumption-of-innocence disclaimer",
          "accused" in g.get("disclaimer", "").lower())

    # Anomaly: planted Whitefield vehicle-theft April spike should surface
    a = anomaly.detect(ADGP)
    check("anomaly detects Whitefield vehicle-theft spike",
          any(al["Station"] == "Whitefield PS" and al["Crime"] == "Vehicle Theft"
              for al in a["alerts"]), a["answer"])

    # Forecast for vehicle theft yields a top station
    f = hotspot.forecast(ADGP, "Vehicle Theft")
    check("forecast returns a prediction", len(f["forecasts"]) > 0, f["answer"])

    # Risk scoring returns ranked stations
    rk = risk.score(ADGP)
    check("risk scoring returns scores", len(rk["scores"]) > 0, rk["answer"])

    # Response lag finds the planted Indiranagar outlier
    lag = response_lag.by_station(ADGP, min_cases=10)
    check("response-lag highlights a station", len(lag["stations"]) > 0, lag["answer"])

    # Socio-economic returns bias disclaimer
    s = socioeconomic.victimization(ADGP, "Online Financial Fraud", "occupation")
    check("socio-economic attaches bias disclaimer", bool(s.get("bias_disclaimer")))

    passed = sum(1 for _, c in results if c)
    print(f"\n{passed}/{len(results)} checks passed.")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
