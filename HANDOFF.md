# HANDOFF — KSP Datathon 2026 (TRINETRA)

Status: **brainstorming done, full plan approved, no code written yet.** Next step was the
synthetic data generator (Phase 1) — not started (tool call interrupted).

---

## What this is

KSP (Karnataka State Police) Datathon 2026. Team is entering **both challenges**, which sit on
the **same Karnataka Police FIR database schema**:

- **Challenge 01** — Intelligent Conversational AI over the crime DB: NL chatbot, English +
  Kannada, voice, context-aware, explainable AI, audit trails, role-based access, PDF export,
  criminal-network viz, crime trend/hotspot, predictive analytics.
- **Challenge 02** — AI-driven Crime Analytics & Visualization platform: dashboards,
  geospatial hotspot maps, district drilldowns, anomaly/trend alerts, link/network analysis,
  repeat-offender tracking, socio-economic correlation, predictive risk scoring.

The two overlap ~70% — same data, same ML brain, differ only in front-end surface.

## Hard constraints (discovered from resources)

- **Deployment on Zoho Catalyst is MANDATORY.** Every capability must use the matching
  Catalyst service or the submission is invalid. Credits via promo **KSPH26**. There is a
  Catalyst hands-on workshop video. Team confirmed Catalyst-ready (credits claimed).
- Submission was ~26 days out at time of brainstorm (≈ late July 2026). In-person finale.
- **Data: schema only so far, no rows released.** Plan assumes we synthesize realistic data
  now and swap real data if/when it drops. ACTION: confirm whether this Drive link holds data
  or just the schema PDF: https://drive.google.com/file/d/1Tmj-kGmYRf5Rngqr7SoWO6zNjCM_MceJ/view

## User decisions locked

- **Unified platform, two faces** (one shared backend/ML, two front-ends).
- Team is **full-stack** (ML/data-science, backend, frontend, GenAI) — no skill limits.
- **Ignore time/scope limits — build the best plan with highest chance of winning.**
- **Win theory = ACTIONABLE + TRUSTWORTHY** (cop can act Monday + defend in court). This is
  the anchor: trust layer (cite/explain/audit/RBAC/ethics) is a first-class differentiator,
  not plumbing.

## User working style (important)

- Caveman mode is ON (terse responses, fragments OK; prose docs/commits written normally).
- Prefers clickable `AskUserQuestion` over numbered questions. Ask when genuinely in doubt.
- Said "don't ask for every step approval" — proceed autonomously through the plan.
- Interrupted the build to request this handoff; check in before resuming heavy work.

---

## Source materials (all in /Users/developer/Downloads/)

- `Police_FIR_ER_Diagram.pdf` — the real FIR schema (fully read; summary below).
- `Datathon 2026 (...).html` — challenge descriptions (5.7MB; strip tags to read).
- `Datathon 2026 ｜ Resources ｜ Hack2skill (...).html` — Catalyst mandate + service table.
- YouTube: https://www.youtube.com/watch?v=eOjfoNp8Mdk (orientation/problem statement),
  https://www.youtube.com/watch?v=embF28oG9q8 ("Hands-on Workshop with Catalyst"). Transcripts
  not extractable via WebFetch.

## FIR schema (key tables — from the ER PDF)

- **CaseMaster** (the FIR): CaseMasterID PK, CrimeNo (structured: 1-digit category + 4 district
  + 4 station/UnitID + 4 year + 5 serial), CaseNo, CrimeRegisteredDate, PolicePersonID→Employee,
  PoliceStationID→Unit, CaseCategoryID, GravityOffenceID (Heinous/Non-Heinous), CrimeMajorHeadID
  →CrimeHead, CrimeMinorHeadID→CrimeSubHead, CaseStatusID, CourtID, IncidentFromDate,
  IncidentToDate, InfoReceivedPSDate, **latitude, longitude**, BriefFacts (free text).
- **ComplainantDetails**: name, AgeYear, OccupationID, ReligionID, CasteID, GenderID (→ socio-
  economic correlation).
- **Victim** / **Accused**: name, AgeYear, GenderID; Accused has PersonID (A1, A2…).
- **ArrestSurrender**: links CaseMasterID, AccusedMasterID, IOID→Employee, CourtID, dates,
  state/district; junction `inv_arrestsurrenderaccused` for arrest↔accused many-to-many.
- **ActSectionAssociation** → Act / Section (IPC etc.). **CrimeHead / CrimeSubHead**.
- **ChargesheetDetails**: cstype CHAR — **A=Chargesheet, B=False Case, C=Undetected** (powers
  detection-quality analytics).
- Masters: CaseCategory (FIR/UDR/PAR/ZeroFIR), GravityOffence, CaseStatusMaster, Court,
  District, State, Unit (police station, self-ref ParentUnit hierarchy), UnitType, Employee
  (IO/officer), Rank, Designation, Caste/Religion/OccupationMaster.
- Relationships: CaseMaster 1-to-many → Victim/Accused/ArrestSurrender/Complainant/
  ActSection; 1-to-1 → Inv_OccuranceTime.

---

## The approved plan (full detail in /Users/developer/.claude/plans/mutable-wibbling-matsumoto.md)

**Concept:** TRINETRA ("third eye" — placeholder name) — one Intelligence Engine, two faces:
- **Copilot** (Ch01): chat/voice/Kannada, cited answers + chart + downloadable PDF brief.
- **War Room** (Ch02): maps/hotspots/network graph/alerts/drilldowns.
Both call the same engine API.

**Trust spine (win anchor):** cite every answer to source FIR row IDs · show the SQL/query run ·
AuditLog table (who asked what) · RBAC scope injected as WHERE (SHO→Unit, DCP→district,
ADGP→state) · confidence + sample-size caveats · bias guardrails.

**Engine modules (each an independent service behind a Router agent):**
Text→SQL (safe/parameterized/whitelisted/RBAC-injected) · RAG over BriefFacts (vector) · Graph
engine (NetworkX/igraph: gangs via community detection, kingpins via centrality, repeat
offenders) · Hotspot forecast (Prophet/STL or LightGBM on lat/long×time) · Anomaly watch
(z-score/EWMA) · Risk score (Zia AutoML) · Detection-quality (cstype B/C rates) · Response-lag
(Incident→InfoReceived→Registered date diffs) · Socio-economic (guardrailed) · Brief generator
(SmartBrowz PDF) · Proactive briefings (Cron→Mail/Push).

**Ethics:** demographic data framed as victimization not profiling; no person-level crime
prediction (forecast places/times only); presumption-of-innocence label on accused; auto-
disclaimers. This stance is itself a differentiator for police judges.

**Catalyst service map:** Web Client Hosting/Slate (2× Next.js front-ends) · Functions + AppSail
(Docker/Python for heavy ML/graph) · Circuits (router orchestration) · Data Store (FIR + audit +
agg) · QuickML (vector/RAG/LLM serving) · Zia AutoML (risk) · Zia Services (Kannada STT/TTS/
translate, OCR) · SmartBrowz (PDF) · Authentication · API Gateway · Stratus (object storage) ·
Cache · Cron→Mail/Push · Signals+Event Functions (new-FIR auto-anomaly) · Pipelines (CI/CD).

**Data strategy:** parameterized **synthetic FIR generator** on the exact schema — real
Karnataka districts/stations w/ lat-long, realistic crime mix + seasonality, and PLANTED
structures so every feature demos: co-accused networks + repeat offenders, geo hotspots, time-
window anomalies, false-case clusters, response-lag outliers, demographic patterns. Loads into
Data Store; doubles as README quickstart. Swap to real data when released.

**Build phases:** 1) Foundation (Catalyst project, Data Store schema + AuditLog, Auth/roles,
API Gateway, synthetic generator + load). 2) Engine core (Text→SQL + RBAC + cite/explain, RAG,
Router, audit) — satisfies most of Ch01. 3) Analytics+ML (graph, forecast, anomaly, risk,
detection-quality, response-lag, socio-economic). 4) Two faces (Copilot + War Room front-ends).
5) Proactive + polish (Cron briefings, Signals, UX, confidence/caveats, disclaimers).
6) Submission package (deploy, demo video, briefs/README, official template, link checks).

**Demo script (~5 min):** SHO login (RBAC scope visible) → Kannada voice "chain-snatching
hotspots my station last month" → map + cited FIRs + SQL shown → flip to War Room → next-week
forecast + patrol rec → network graph (repeat-offender chain + gang cluster, innocence label) →
anomaly alert (vehicle-theft spike) → detection-quality panel (high false-case station) →
generate+download PDF → audit log → escalate to DCP (scope widens) → sample proactive email.

**Submission deliverables (official):** Prototype Brief (problem/features/stack/impact) · public
GitHub repo (source + README + setup + synthetic-data quickstart) · demo video (public Drive or
unlisted YouTube) · **live deployment exclusively on Catalyst** · filled official submission
template (download from organizer link) · all links verified accessible (incognito).

---

## Environment

- Working dir: `/Users/developer/Documents/Projects/KSP_Datathon` (NOT a git repo yet — empty).
- Platform: macOS (darwin), shell: fish.
- Python env state UNKNOWN (the check for faker/pandas was interrupted — verify before coding).
- Plan file: `/Users/developer/.claude/plans/mutable-wibbling-matsumoto.md`.

## Immediate next steps for fresh agent

1. Confirm with user whether to start building, and confirm the Drive link's contents (data vs
   schema only).
2. Phase 1 first concrete artifact (needs no Catalyst creds): **synthetic FIR data generator**
   in Python matching the schema above, with planted demo structures. Verify python env first
   (`pandas`, `faker` likely needed; user uses `rtk` proxy for shell commands).
3. Then scaffold Catalyst project + Data Store schema and load generated data.

## Open questions

- Real data: provided where/when? (check Drive link).
- Exact submission deadline + finale date (≈ late July 2026 inferred).
- Confirm product name (TRINETRA is a placeholder).
- Which LLM is allowed inside Catalyst QuickML serving (affects Router/Text→SQL choice).
