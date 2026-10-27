# Catalyst Service Mapping — TRINETRA

**Deployment on Zoho Catalyst is mandatory** for the KSP Datathon 2026: every capability must
map to the matching Catalyst service or the submission is invalid (credits claimed via promo
**KSPH26**). This document maps each TRINETRA engine module / feature in *this* prototype to the
Catalyst service it will run on in production. The local prototype uses FastAPI + SQLite + Vite as
a drop-in stand-in for these services; the mapping below is the migration target (see
[`../gaps.md`](../gaps.md) for what is not yet deployed).

---

## Layer → Catalyst service

| TRINETRA layer / feature | Catalyst service | Prototype stand-in today |
|---|---|---|
| Copilot + War Room front-ends | **Web Client Hosting / Slate** | Vite dev server (React SPA, 3 tabs) |
| Engine modules (Text→SQL, RAG, anomaly, detection-quality, response-lag, socio-economic) | **Serverless Functions** | FastAPI route handlers |
| Heavy ML / graph (NetworkX graph engine, forecast, risk scoring) | **AppSail** (Docker / Python) | FastAPI in-process modules |
| Router pipeline orchestration | **Circuits** | `router.py` (in-process dispatcher) |
| FIR data + full-text + audit log | **Data Store** | SQLite `trinetra.db` (FIR + AuditLog) |
| Vector / RAG / LLM serving | **QuickML** | deterministic embedding/keyword RAG in `rag.py` |
| Risk-score tabular ML | **Zia AutoML** | scikit-learn composite score in `risk.py` |
| Kannada STT / TTS / translate, OCR | **Zia Services** | static i18n + phrase map + browser Web Speech API |
| PDF briefs / screenshots | **SmartBrowz** | reportlab in `brief_pdf.py` |
| Auth / login | **Authentication** | demo role switch (no real auth backend) |
| Route / throttle / auth in front of functions | **API Gateway** | Vite `/api` proxy → FastAPI |
| Object storage (generated PDFs) | **Stratus** | in-memory response stream |
| Query cache | **Cache** | none (queries are fast/offline) |
| Scheduled briefings (station digests) | **Cron → Mail / Push** | not wired (planned) |
| New-FIR → auto anomaly check | **Signals + Event Functions** | manual anomaly scan endpoint |
| CI / CD | **Pipelines** | local `run.sh` |

---

## Module → service detail

| Module (`backend/app/modules/`) | Catalyst service | Notes |
|---|---|---|
| `router.py` | Circuits | orchestrates module selection + answer composition |
| `text2sql.py` | Functions + QuickML | schema-grounded NL→SQL; QuickML serves the LLM Text→SQL in prod |
| `rag.py` | QuickML | vector index over `BriefFacts` |
| `graph_engine.py` | AppSail | NetworkX community detection + centrality (CPU-heavy) |
| `hotspot.py` | AppSail | spatio-temporal forecast (Prophet/LightGBM target in prod) |
| `anomaly.py` | Functions + Signals | z-score scan; Signals triggers it on new-FIR events |
| `risk.py` | Zia AutoML | tabular patrol-risk model |
| `detection_quality.py` | Functions + Data Store | aggregates on `ChargesheetDetails.cstype` |
| `response_lag.py` | Functions + Data Store | date-diff aggregates |
| `socioeconomic.py` | Functions | guardrailed aggregates + bias note |
| `brief_pdf.py` | SmartBrowz + Stratus | render PDF, store in object storage |
| `audit.py` | Data Store | append-only AuditLog table |
| `rbac.py` | Authentication + API Gateway | role → scope `WHERE` injection |

---

## Migration order (recommended)

1. **Data Store** — load the synthetic (then real) FIR rows + AuditLog schema.
2. **Functions + AppSail** — lift the engine modules; heavy graph/ML to AppSail.
3. **API Gateway + Authentication** — front the functions, add real RBAC.
4. **Slate / Web Client Hosting** — deploy the two front-ends.
5. **QuickML + Zia AutoML + Zia Services** — swap the deterministic stand-ins for real ML/LLM/voice.
6. **Cron, Signals, SmartBrowz, Stratus, Cache, Pipelines** — proactive + polish + CI/CD.
