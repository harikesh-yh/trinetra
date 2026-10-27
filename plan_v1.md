# TRINETRA — KSP Datathon 2026 Winning Plan

## Context

KSP Datathon 2026 has two challenges, both built on the **same Karnataka Police FIR
database schema** (real ER diagram provided; data rows not yet released):

- **Challenge 01** — Intelligent Conversational AI over the crime database (NL + Kannada +
  voice chatbot, explainable, audit trails, role-based access, PDF export, network viz,
  predictive analytics).
- **Challenge 02** — AI-driven Crime Analytics & Visualization platform (dashboards,
  geospatial hotspots, district drilldowns, anomaly alerts, link/network analysis, repeat
  offender tracking, socio-economic correlation, predictive risk scoring).

The two challenges overlap ~70% (same data, same ML brain; they differ only in front-end
surface). We are entering **both**. **Deployment on Zoho Catalyst is mandatory** — every
capability must use the matching Catalyst service or the submission is invalid (credits
claimed via promo KSPH26).

**Win theory (chosen by user): actionable + trustworthy.** A police officer must be able to
act on an answer Monday morning and defend it in court. No time/scope constraints imposed —
go for the highest probability of winning both challenges.

**Outcome intended:** one shared Intelligence Engine ("one brain") exposed through two
front-ends ("two faces") — the **Copilot** (Ch01) and the **War Room** (Ch02) — deployed
end-to-end on Catalyst, with a trust layer (cite/explain/audit/RBAC/ethics) as the spine.

---

## Architecture

```
 Copilot (Next.js)            War Room (Next.js)
  chat / voice / Kannada       maps / graph / alerts / drilldown
         \                          /
          \____ Catalyst API Gateway ___/
                       |
            INTELLIGENCE ENGINE  (Catalyst Functions + AppSail)
   ┌──────────────────────────────────────────────────────────┐
   │ Router agent  →  selects + composes tools                 │
   │  Text→SQL · RAG(BriefFacts) · Graph · Forecast            │
   │  Anomaly · RiskScore · Detection-quality · Response-lag    │
   │  Socio-economic · Brief generator · Proactive briefings    │
   │  TRUST LAYER: cite · explain · audit · RBAC · guardrails   │
   └──────────────────────────────────────────────────────────┘
              Catalyst Data Store (FIR + feature/agg + audit)
              QuickML (vector/RAG/LLM) · Stratus · Cache
```

Each module is an **independent service behind the Router** — testable alone, swappable,
composable. Build the brain once; both faces call the same engine API.

---

## The Trust Spine (the win anchor — every feature rides this)

| Pillar | Implementation |
|---|---|
| Cite everything | every number/answer carries source FIR row IDs, clickable to the record |
| Show the work | display the SQL / graph query that produced the answer |
| Audit trail | `AuditLog` table in Data Store: user, role, question, query, timestamp, scope |
| Role scope (RBAC) | injected `WHERE` clause by role: SHO→own Unit, DCP→district, ADGP→state |
| Confidence + caveats | sample size + low-confidence flag surfaced with each result |
| Bias guardrail | demographic dimensions flagged; framed as victimization, not profiling |

---

## Intelligence Engine modules

| Module | Function | Build |
|---|---|---|
| **Router agent** | reads question, picks + sequences tools, composes answer | LLM via QuickML serving; orchestrated by Catalyst Circuits |
| **Text→SQL** | NL→safe parameterized SQL on FIR schema; read-only, table/col whitelist, row-limit, RBAC `WHERE` injected | LLM + schema-grounded prompt |
| **RAG / BriefFacts** | semantic search over case narratives; "find similar MO" | vector index on `CaseMaster.BriefFacts` (QuickML RAG) |
| **Graph engine** | co-accused + IO + location network; community detection (gangs), centrality (kingpins/bridges), repeat-offender ranking | NetworkX/igraph in AppSail (Python) |
| **Hotspot forecast** | spatio-temporal next-period risk per grid/station | Prophet/STL or LightGBM on lat/long × time |
| **Anomaly watch** | spike detection per crime type × area × time | rolling z-score / EWMA |
| **Risk score** | area+time risk for patrol allocation | Zia AutoML (tabular) |
| **Detection-quality** | false-case (cstype=B) / undetected (cstype=C) rates by station/IO/crime | aggregates on `ChargesheetDetails` |
| **Response-lag** | Incident→InfoReceived→Registered gaps; underreporting signal | date-diff aggregates |
| **Socio-economic** | victimization patterns by occupation/age/religion/caste (guardrailed) | aggregates + bias note |
| **Brief generator** | answer/dashboard → downloadable PDF report | Catalyst SmartBrowz |
| **Proactive briefings** | scheduled station digest: new hotspots, repeat offenders active, anomalies | Cron → Mail/Push |

### Schema hooks (why each module is feasible)
- lat/long + District/State + Unit hierarchy → maps, hotspots, drilldown.
- IncidentFrom/To, InfoReceivedPSDate, CrimeRegisteredDate → trends, seasonality, response-lag.
- Accused ↔ Case ↔ co-accused, ArrestSurrender(IO, court), `inv_arrestsurrenderaccused`
  junction → network graph, gangs, repeat offenders.
- ComplainantDetails Age/Occupation/Religion/Caste/Gender + Victim/Accused demographics →
  socio-economic correlation.
- CrimeHead/SubHead, Act/Section, GravityOffence(Heinous) → classification, severity.
- CaseStatus + ChargesheetDetails.cstype (A/B/C) → clearance, false-case, detection rate.
- BriefFacts free text → RAG, semantic similarity, narrative Q&A.
- Employee/IO links → officer workload/performance.

---

## Ethics / guardrails (defensible = trustworthy, itself a differentiator)

- Caste/religion/occupation queries framed as **victimization & resource-targeting**, never
  predictive policing on individuals/groups; auto-disclaimer attached.
- **No "predict who will commit crime" on persons.** Forecasting targets **places/times**.
- Bias note surfaced whenever a demographic dimension is used.
- Presumption-of-innocence label on accused in all network views (accused ≠ convicted).
- Audit + RBAC prevent fishing / misuse.

---

## Catalyst service mapping (mandatory deploy; uses platform fully)

| Layer | Catalyst service |
|---|---|
| Front-ends (2× Next.js) | Web Client Hosting / Slate |
| Engine modules | Serverless Functions; heavy ML/graph → AppSail (Docker/Python) |
| Router pipeline orchestration | Circuits |
| FIR data + full-text + audit log | Data Store |
| Vector / RAG / LLM serving | QuickML |
| Risk-score tabular ML | Zia AutoML |
| Kannada STT/TTS/translate, OCR | Zia Services |
| PDF briefs / screenshots | SmartBrowz |
| Auth / login | Authentication |
| Route / throttle / auth in front of functions | API Gateway |
| Object storage (PDFs) | Stratus |
| Query cache | Cache |
| Scheduled briefings | Cron → Mail / Push |
| New-FIR → auto anomaly check | Signals + Event Functions |
| CI/CD | Pipelines |

---

## Data strategy (no rows released yet)

Build a **parameterized synthetic FIR generator** matching the exact ER schema:
- Real Karnataka districts/police stations with realistic lat-long.
- Realistic crime-type mix, temporal trends + seasonality.
- **Planted** structures so every feature has something to demo: co-accused networks +
  repeat offenders, geographic hotspots, time-window anomalies/spikes, false-case clusters,
  response-lag outliers, demographic victimization patterns.
- Output loads directly into Catalyst Data Store; generator parameters documented.

Swap to real data when organizers release it (confirm whether the Resources Drive link holds
data or only the schema PDF). Generator doubles as the README "quickstart with sample data."

---

## Build phases

1. **Foundation** — Catalyst project, Data Store schema (FIR tables + AuditLog + feature/agg
   tables), Auth + roles, API Gateway skeleton, synthetic data generator + load.
2. **Engine core** — Text→SQL (with RBAC/whitelist/cite/explain), RAG over BriefFacts,
   Router agent, audit logging. This alone satisfies most of Ch01.
3. **Analytics + ML** — Graph engine, hotspot forecast, anomaly watch, risk score,
   detection-quality, response-lag, socio-economic. Feeds War Room + Copilot tools.
4. **Two faces** — Copilot front-end (chat/voice/Kannada via Zia, cited answers, PDF via
   SmartBrowz); War Room front-end (maps, network graph, drilldowns, alerts, panels).
5. **Proactive + polish** — Cron briefings + Mail/Push, Signals auto-anomaly, demo-grade UX,
   confidence/caveat surfacing, ethics disclaimers.
6. **Submission package** — deploy all on Catalyst, record demo, write briefs/README, fill
   official template, verify every link.

---

## Demo script (the room, ~5 min)

1. SHO login → restricted scope visible (RBAC).
2. Kannada voice: "chain-snatching hotspots in my station last month" → map + cited FIRs +
   the SQL shown.
3. Flip to War Room → next-week hotspot forecast + patrol recommendation.
4. Network graph → repeat-offender chain + gang community; click accused → linked cases
   (presumption-of-innocence label).
5. Anomaly alert fires → vehicle-theft spike in district X.
6. Detection-quality panel → station with high false-case rate.
7. Generate + download PDF brief (SmartBrowz).
8. Show audit log; escalate scope to DCP → data widens.
9. Show sample proactive email digest (Cron + Mail).

---

## Submission deliverables (per official guidelines)

- **Prototype Brief** — problem statement, key features, tech stack, impact/use case.
- **Public GitHub repo** — complete source, README, setup + execution instructions,
  synthetic-data quickstart.
- **Demo video** — public (Drive/unlisted YouTube): problem overview, working prototype,
  key workflows.
- **Deployed link** — live, **exclusively on Catalyst**.
- **Official submission template** — filled (download from organizer link).
- **Completeness** — every link tested + accessible before submission.

---

## Verification

- **Per module:** unit tests each engine service in isolation (Text→SQL on a fixed question
  bank → expected SQL/result; graph metrics on a known synthetic network; forecast/anomaly
  on planted signals; RBAC scope-injection tests; audit-log write tests).
- **End-to-end:** run the demo script against the deployed Catalyst instance; confirm each of
  the 9 steps works live with cited sources and audit entries recorded.
- **Trust checks:** every answer shows source FIR IDs + the query; RBAC scope enforced per
  role; demographic queries emit the bias disclaimer.
- **Submission gate:** all five deliverables present; GitHub + demo + deployed links open in
  an incognito browser (public access).
