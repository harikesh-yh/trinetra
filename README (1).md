# TRINETRA — KSP Datathon 2026

**One Intelligence Engine, two faces.** A trustworthy, actionable crime-intelligence
platform built on the Karnataka State Police FIR database schema. TRINETRA ("third eye")
answers a police officer's questions in natural language **and** powers an analytics War
Room — both off the *same* engine, with a trust spine (cite · explain · audit · RBAC ·
ethics) wired through every answer.

This repository is the **working local prototype** for the KSP Datathon 2026
(Challenge 01 *Conversational AI* + Challenge 02 *Crime Analytics & Visualization*). The
mandatory Zoho Catalyst deployment is mapped service-by-service in
[`CATALYST_MAPPING.md`](./CATALYST_MAPPING.md); what remains versus the full winning plan is
tracked honestly in [`../gaps.md`](../gaps.md).

---

## One-command quickstart

```bash
# from the repo root (the folder that contains this trinetra/ directory)
./trinetra/run.sh
```

`run.sh` installs backend dependencies, generates the synthetic FIR database, starts the
FastAPI engine on **:8077**, installs the frontend, and starts the Vite dev server on
**:5173** (Vite proxies `/api` → `:8077`). Open <http://127.0.0.1:5173/>.

### Manual steps (what run.sh does)

**Backend (FastAPI engine):**

```bash
cd trinetra/backend
python3 -m pip install -r requirements.txt
python3 generate_data.py            # builds trinetra.db: 4000 synthetic FIRs
python3 -m uvicorn app.main:app --port 8077
```

**Frontend (React + Vite + TypeScript):**

```bash
cd trinetra/frontend
npm install
npm run dev                         # http://127.0.0.1:5173
```

**Smoke tests (13 engine checks, all planted demo facts):**

```bash
cd trinetra/backend
python3 -m tests.test_engine        # expect "13/13 checks passed."
```

---

## Architecture overview

```
 Copilot (React)              War Room (React)
  chat / voice / Kannada       maps / network graph / alerts / drilldowns
         \                          /
          \____ Vite proxy /api ___/         (→ Catalyst API Gateway in prod)
                       |
            INTELLIGENCE ENGINE  (FastAPI; → Catalyst Functions + AppSail)
   ┌──────────────────────────────────────────────────────────┐
   │ Router agent  →  selects + composes the right module      │
   │  Text→SQL · RAG(BriefFacts) · Graph · Forecast            │
   │  Anomaly · RiskScore · Detection-quality · Response-lag    │
   │  Socio-economic · Brief generator (PDF)                    │
   │  TRUST LAYER: cite · explain · audit · RBAC · guardrails   │
   └──────────────────────────────────────────────────────────┘
              SQLite (FIR + audit)   (→ Catalyst Data Store in prod)
```

Every module is an independent service behind the **Router**. The frontend is a single SPA
with three tabs — **Copilot**, **War Room**, **Audit Log** — both "faces" share one backend.

### Engine modules (`trinetra/backend/app/modules/`)

| Module | What it does |
|---|---|
| `router.py` | reads the question, picks + sequences the right module, composes the cited answer |
| `text2sql.py` | NL → safe, parameterized, whitelisted SQL with RBAC `WHERE` injected; returns the SQL it ran |
| `rag.py` | semantic search over `BriefFacts` ("find similar modus operandi") |
| `graph_engine.py` | co-accused network (NetworkX): community detection (gangs), centrality (kingpins), repeat offenders |
| `hotspot.py` | geospatial hotspots + next-month forecast (moving-average / linear trend) |
| `anomaly.py` | per crime × station × month spike detection (z-score) |
| `risk.py` | composite patrol-risk score per station |
| `detection_quality.py` | chargesheet / false-case / undetected rates from `cstype` A/B/C |
| `response_lag.py` | Incident → InfoReceived → Registered date gaps (underreporting signal) |
| `socioeconomic.py` | guardrailed victimization patterns (with bias disclaimer) |
| `brief_pdf.py` | renders any answer to a downloadable PDF brief (reportlab) |

### Trust spine

- **Cite** — every answer carries source FIR IDs (`cited_ids`).
- **Explain** — the exact SQL / query is returned and shown.
- **Audit** — every request writes to the `AuditLog` (user, role, question, query, scope, time).
- **RBAC** — a scope `WHERE` clause is injected by role (see below).
- **Confidence + caveats** — sample size and a low-confidence flag are surfaced.
- **Ethics** — demographics framed as *victimization*, never profiling; presumption-of-innocence
  label on all accused; no person-level crime prediction (forecasts target places/times).

---

## Demo users (RBAC scope)

| Username | Role | Scope |
|---|---|---|
| `sho_koramangala` | SHO | one station — **Koramangala PS** |
| `dcp_bengaluru` | DCP | one district — **Bengaluru City** |
| `adgp_state` | ADGP | whole state — **Karnataka** (full access) |

The same question returns more rows as scope widens; the injected scope is recorded in the
audit log so it is defensible.

### Planted demo facts (in the synthetic data)

- **Koramangala** — chain-snatching hotspot.
- **Whitefield** — April 2026 vehicle-theft anomaly spike.
- **Electronic City** — high false-case (`cstype=B`) cluster.
- **Indiranagar** — response-lag (registration-delay) outlier.
- Co-accused **gangs** + **repeat offenders** seeded into the network graph.

---

## Demo script (~5 minutes, 9 steps)

1. **Sign in as SHO** (`sho_koramangala`) — note the restricted scope chip (one station).
2. In **Copilot**, ask *"chain snatching hotspots last month"* → cited FIRs + the SQL that ran +
   a chart + a confidence/caveat line.
3. Flip to **War Room** → geospatial hotspot map + next-month **forecast** with a patrol
   recommendation.
4. **Criminal Network Analysis** → gang communities, suspected kingpins (centrality) and
   repeat offenders, with the presumption-of-innocence disclaimer.
5. **Anomaly Alerts** → the Whitefield vehicle-theft spike fires (high severity).
6. **Detection Quality** → Electronic City PS surfaces with a ~50% false-case rate.
7. **Download PDF brief** from a Copilot answer (court-ready export).
8. Open the **Audit Log** tab → every question/query/scope is recorded.
9. **Escalate to ADGP** (`adgp_state`) — re-run the same questions; the scope widens to the
   whole state and the dashboards fill in.

---

## Trust & ethics summary

TRINETRA is built to be **actionable** (a cop can act on it Monday) **and trustworthy** (it can
be defended in court). Demographic dimensions are framed as victimization and resource-targeting,
never as predictive policing on individuals or groups, and always carry a bias disclaimer.
There is no person-level crime prediction — forecasting targets places and times only. Accused
persons are labelled with a presumption-of-innocence note everywhere they appear. RBAC and the
audit trail together prevent fishing and misuse. This stance is a first-class differentiator,
not an afterthought.

---

## Tech stack

- **Backend:** Python 3.9, FastAPI, Uvicorn, SQLite, scikit-learn, NetworkX, pandas, Faker, reportlab.
- **Frontend:** React 18, Vite 5, TypeScript, Leaflet (maps), Recharts (charts), vis-network (graph).
- **Data:** 4000 synthetic FIRs across 40 stations / 15 districts on the real KSP FIR schema.

See [`CATALYST_MAPPING.md`](./CATALYST_MAPPING.md) for the mandatory Zoho Catalyst deployment
mapping and [`../gaps.md`](../gaps.md) for the honest gap list versus the full winning plan.
