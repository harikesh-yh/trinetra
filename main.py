"""TRINETRA Intelligence Engine - FastAPI gateway.

One engine, two faces. All endpoints enforce RBAC scope and write to the audit
log. The deterministic, offline modules power every capability; an optional LLM
key can later widen NL coverage without changing this surface.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import audit
from .db import db_exists
from .modules import (anomaly, brief_pdf, detection_quality, graph_engine,
                      hotspot, response_lag, risk, router, socioeconomic)
from .rbac import DEMO_USERS, User

app = FastAPI(title="TRINETRA Intelligence Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _user(username: str) -> User:
    u = DEMO_USERS.get(username)
    if not u:
        raise HTTPException(status_code=401, detail="Unknown user")
    return u


class AskRequest(BaseModel):
    username: str
    question: str


class BriefRequest(BaseModel):
    username: str
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "db": db_exists()}


@app.get("/users")
def users():
    return [{"username": u.username, "role": u.role, "scope": u.scope_label}
            for u in DEMO_USERS.values()]


@app.post("/login")
def login(body: dict):
    u = _user(body.get("username", ""))
    return {"username": u.username, "role": u.role, "scope": u.scope_label}


@app.post("/ask")
def ask(req: AskRequest):
    user = _user(req.username)
    result = router.route(user, req.question)
    audit.log(user, req.question, result.get("route", result.get("module", "router")),
              result.get("sql", ""))
    return result


@app.get("/graph")
def graph(username: str):
    user = _user(username)
    result = graph_engine.analyze(user)
    audit.log(user, "criminal network analysis", "Graph engine")
    return result


@app.get("/hotspots")
def hotspots(username: str, crime: Optional[str] = None, days: int = 90):
    user = _user(username)
    result = hotspot.hotspots(user, crime, days)
    audit.log(user, f"hotspots crime={crime} days={days}", "Hotspot")
    return result


@app.get("/forecast")
def forecast(username: str, crime: Optional[str] = None):
    user = _user(username)
    result = hotspot.forecast(user, crime)
    audit.log(user, f"forecast crime={crime}", "Forecast")
    return result


@app.get("/anomalies")
def anomalies(username: str):
    user = _user(username)
    result = anomaly.detect(user)
    audit.log(user, "anomaly scan", "Anomaly watch")
    return result


@app.get("/risk")
def risk_scores(username: str):
    user = _user(username)
    result = risk.score(user)
    audit.log(user, "patrol risk scoring", "Risk score")
    return result


@app.get("/detection-quality")
def detection(username: str):
    user = _user(username)
    result = detection_quality.by_station(user)
    audit.log(user, "detection quality", "Detection quality")
    return result


@app.get("/response-lag")
def lag(username: str):
    user = _user(username)
    result = response_lag.by_station(user)
    audit.log(user, "response lag", "Response lag")
    return result


@app.get("/socioeconomic")
def socio(username: str, crime: Optional[str] = None, dimension: str = "occupation"):
    user = _user(username)
    result = socioeconomic.victimization(user, crime, dimension)
    audit.log(user, f"socioeconomic crime={crime} dim={dimension}", "Socio-economic")
    return result


@app.get("/audit")
def audit_log(username: str, limit: int = 50):
    _user(username)  # validate
    return {"entries": audit.recent(limit)}


@app.post("/brief.pdf")
def brief(req: BriefRequest):
    user = _user(req.username)
    payload = router.route(user, req.question)
    audit.log(user, req.question, "PDF brief", payload.get("sql", ""))
    pdf = brief_pdf.build_brief(user, req.question, payload)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=trinetra_brief.pdf"})
