#!/usr/bin/env python3
"""Fill the official KSP Datathon 2026 submission template for TRINETRA.

Opens the official template, adds a body text box (and screenshots on the
snapshots slide) to each content slide, and saves a NEW file to
trinetra/submission/TRINETRA_Submission.pptx (the original is never modified).

Usage:  python3 scripts/fill_template.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "KSP Datathon 2026 _ Prototype Submission Template.pptx"
OUT = ROOT / "trinetra" / "submission" / "TRINETRA_Submission.pptx"
SHOTS = ROOT / "trinetra" / "submission" / "screenshots"

DARK = RGBColor(0x1A, 0x1A, 0x2E)

# ---- Body content per slide (1-indexed). Each is a list of (text, level). ----
# level 0 = top bullet, level 1 = sub-bullet, level None = plain heading line.
BODIES: dict[int, list[tuple[str, int | None]]] = {
    2: [  # Brief about the solution
        ("TRINETRA (\"third eye\") is one Intelligence Engine with two faces:", None),
        ("Copilot (Challenge 01): a conversational AI over the Karnataka Police FIR "
         "database \u2014 English + Kannada, voice-enabled, with cited answers, the SQL "
         "shown, charts, and downloadable PDF briefs.", 0),
        ("War Room (Challenge 02): an analytics platform \u2014 geospatial hotspot maps, "
         "criminal-network graph, anomaly alerts, detection-quality and response-lag "
         "panels, and district drilldowns.", 0),
        ("Both faces call the SAME engine API, so one ML brain powers both challenges. "
         "A trust spine (cite \u00b7 explain \u00b7 audit \u00b7 RBAC \u00b7 ethics) runs "
         "through every answer.", 0),
    ],
    3: [  # Opportunities / USP
        ("USP \u2014 the Trust Spine makes answers actionable AND court-defensible:", None),
        ("Cite: every answer carries source FIR row IDs.", 0),
        ("Explain: the exact SQL / query that produced the answer is shown.", 0),
        ("Audit: every question, query, role and data scope is logged.", 0),
        ("RBAC: a scope WHERE clause is injected by role (SHO\u2192station, "
         "DCP\u2192district, ADGP\u2192state).", 0),
        ("Ethics: demographics framed as victimization not profiling; "
         "presumption-of-innocence on accused; no person-level prediction.", 0),
        ("Differentiator: unlike static dashboards, a cop can act on it Monday morning "
         "and defend it in court. One engine serves both challenges.", 0),
    ],
    4: [  # Feature list
        ("Engine modules (one brain behind a Router agent):", None),
        ("Text\u2192SQL (safe, parameterized, whitelisted, RBAC-injected) \u00b7 RAG over "
         "BriefFacts (similar MO) \u00b7 Criminal-network graph (gangs, kingpins, repeat "
         "offenders).", 0),
        ("Hotspot forecast \u00b7 Anomaly watch \u00b7 Patrol risk score \u00b7 "
         "Detection-quality (false-case / undetected) \u00b7 Response-lag \u00b7 "
         "Socio-economic (guardrailed) \u00b7 PDF brief generator.", 0),
        ("Copilot face: chat + voice + Kannada, citations, explainable SQL, charts, "
         "PDF export.", 0),
        ("War Room face: hotspot maps, network graph, anomaly alerts, detection-quality "
         "and response-lag panels, risk scores, drilldowns.", 0),
    ],
    5: [  # Process / use-case flow
        ("Use-case flow (every request rides the trust spine):", None),
        ("1. Officer signs in \u2192 RBAC resolves their data scope (station / district / "
         "state).", 0),
        ("2. Question (typed or spoken, EN/KN) \u2192 Router agent reads intent and picks "
         "the right module.", 0),
        ("3. Module runs (e.g. Text\u2192SQL builds safe SQL with the scope WHERE "
         "injected; graph/forecast/anomaly as needed).", 0),
        ("4. Answer is composed with cited FIR IDs + the SQL shown + a chart + a "
         "confidence/caveat line.", 0),
        ("5. The question, query and scope are written to the Audit Log; an optional PDF "
         "brief can be downloaded.", 0),
    ],
    7: [  # Architecture
        ("Two front-ends (Copilot + War Room) \u2192 API Gateway \u2192 Intelligence "
         "Engine \u2192 Data Store.", None),
        ("Intelligence Engine (Catalyst Functions + AppSail): a Router agent selects and "
         "composes modules \u2014 Text\u2192SQL, RAG, Graph, Forecast, Anomaly, Risk, "
         "Detection-quality, Response-lag, Socio-economic, Brief generator.", 0),
        ("Trust layer wraps every module: cite \u00b7 explain \u00b7 audit \u00b7 RBAC "
         "\u00b7 guardrails.", 0),
        ("Data Store holds FIR rows + audit log; QuickML serves vector/RAG/LLM; Stratus "
         "+ Cache support storage and speed.", 0),
        ("Prototype today: FastAPI engine + SQLite + React/Vite SPA, a 1:1 stand-in for "
         "the Catalyst services above.", 0),
    ],
    8: [  # Technologies
        ("Backend / Engine:", None),
        ("Python, FastAPI, Uvicorn, SQLite, scikit-learn, NetworkX, pandas, Faker, "
         "reportlab.", 0),
        ("Frontend:", None),
        ("React 18, Vite 5, TypeScript, Leaflet (maps), Recharts (charts), vis-network "
         "(graph).", 0),
        ("Target platform: Zoho Catalyst (Data Store, Functions/AppSail, Slate, QuickML, "
         "Zia AutoML, Zia Services, SmartBrowz, Authentication, API Gateway, Stratus, "
         "Cache, Cron, Signals, Pipelines).", 0),
    ],
    9: [  # Catalyst services
        ("Mandatory Zoho Catalyst service mapping (full detail in CATALYST_MAPPING.md):", None),
        ("Web Client Hosting / Slate \u2014 the two front-ends.", 0),
        ("Functions + AppSail \u2014 engine modules; heavy graph/ML on AppSail.", 0),
        ("Circuits \u2014 Router pipeline orchestration.", 0),
        ("Data Store \u2014 FIR data + full-text + audit log.", 0),
        ("QuickML \u2014 vector / RAG / LLM serving (Text\u2192SQL).", 0),
        ("Zia AutoML \u2014 patrol risk scoring; Zia Services \u2014 Kannada STT/TTS/"
         "translate + OCR.", 0),
        ("SmartBrowz \u2014 PDF briefs; Authentication \u2014 login/RBAC; API Gateway \u2014 "
         "routing/throttling.", 0),
        ("Stratus \u2014 object storage; Cache \u2014 query cache; Cron\u2192Mail/Push \u2014 "
         "proactive briefings.", 0),
        ("Signals + Event Functions \u2014 new-FIR auto-anomaly; Pipelines \u2014 CI/CD.", 0),
    ],
    12: [  # Benchmarking
        ("Prototype performance / benchmarking:", None),
        ("Dataset: 4000 synthetic FIRs across 40 police stations and 15 districts, "
         "generated on the real KSP FIR ER schema.", 0),
        ("Planted, verifiable demo signals: Koramangala chain-snatching hotspot; "
         "Whitefield April vehicle-theft spike; Electronic City ~50% false-case cluster; "
         "Indiranagar response-lag outlier; gangs + repeat offenders in the graph.", 0),
        ("Engine is deterministic and fully offline \u2014 sub-second response on a "
         "laptop, no external API calls in the demo path.", 0),
        ("Quality: 13/13 engine smoke tests passing (RBAC scope narrowing, citations, "
         "SQL returned, planted-fact discovery, bias/innocence disclaimers).", 0),
    ],
    13: [  # Links
        ("GitHub Public Repository: https://github.com/Collaborator/KSP", 0),
        ("Demo Video Link (3 minutes): [PLACEHOLDER \u2014 record + paste public "
         "Drive/YouTube link]", 0),
        ("Deployed Link: [PLACEHOLDER \u2014 pending Zoho Catalyst deployment; see "
         "CATALYST_MAPPING.md]", 0),
    ],
    14: [  # Future development
        ("Future development (full honest gap list in gaps.md):", None),
        ("Deploy end-to-end on Zoho Catalyst (Data Store, Functions/AppSail, Slate, API "
         "Gateway, Authentication).", 0),
        ("Integrate real KSP FIR data when released (swap the synthetic generator).", 0),
        ("Real LLM Text\u2192SQL via QuickML (replace deterministic intent matching); "
         "real Zia Kannada STT/TTS/translate.", 0),
        ("Upgrade forecast to Prophet/LightGBM and risk to Zia AutoML; vector RAG store.", 0),
        ("Wire Cron proactive briefings + Signals auto-anomaly; expand tests + Pipelines "
         "CI/CD.", 0),
        ("Produce the demo video and fill the live deployed link for submission.", 0),
    ],
}

# Slide 1 team details (appended into the existing text box).
TEAM = {
    "Team name": "TRINETRA",
    "Team leader name": "[PLACEHOLDER \u2014 confirm team leader name]",
    "Team size": "[PLACEHOLDER \u2014 confirm team size]",
    "Problem Statement": "KSP Datathon 2026 \u2014 Challenge 01 (Intelligent Conversational AI "
                         "over the crime database) AND Challenge 02 (AI-driven Crime Analytics "
                         "& Visualization platform).",
}


def add_body(slide, items, top=1.7, height=3.6, font=12):
    """Add a body text box with bulleted items to a slide."""
    box = slide.shapes.add_textbox(Inches(0.4), Inches(top), Inches(9.2), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for text, level in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font)
        run.font.color.rgb = DARK
        if level is None:
            run.font.bold = True
            p.level = 0
        else:
            p.level = min(level, 4)
        p.space_after = Pt(4)
    return box


def fill_slide1(slide):
    """Append team values onto the Team Details text box."""
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        if "Team Details" in sh.text_frame.text:
            tf = sh.text_frame
            for p in tf.paragraphs:
                line = p.text.strip()
                for key, val in TEAM.items():
                    if line.rstrip(":").strip().lower() == key.lower() or line.lower().startswith(key.lower() + ":"):
                        # Append the value to this paragraph.
                        run = p.add_run()
                        run.text = " " + val
                        run.font.bold = False
                        if p.runs:
                            run.font.size = p.runs[0].font.size or Pt(14)
            return True
    return False


def fill_snapshots(slide):
    """Slide 11: add the captured screenshots in a 2-column grid (+ caption)."""
    shots = sorted(SHOTS.glob("*.png")) if SHOTS.is_dir() else []
    if not shots:
        add_body(slide, [("[PLACEHOLDER \u2014 prototype screenshots not captured]", 0)], top=2.0)
        return 0
    captions = {
        "01_login": "Login \u2014 RBAC role selection",
        "02_copilot_answer": "Copilot \u2014 cited answer + SQL + chart + confidence",
        "03_warroom": "War Room dashboard",
        "04_network_graph": "Criminal network \u2014 kingpins + repeat offenders",
        "05_audit_log": "Audit Log",
    }
    # Row 1: up to 3 thumbnails (~3.0" wide); Row 2: remaining centered.
    w = Inches(3.0)
    row1 = shots[:3]
    row2 = shots[3:6]

    def lefts(n):
        gap = 0.25
        total = n * 3.0 + (n - 1) * gap
        start = (10.0 - total) / 2
        return [start + i * (3.0 + gap) for i in range(n)]

    placed = 0
    for left, shot in zip(lefts(len(row1)), row1):
        slide.shapes.add_picture(str(shot), Inches(left), Inches(1.55), width=w)
        placed += 1
    for left, shot in zip(lefts(len(row2)), row2):
        slide.shapes.add_picture(str(shot), Inches(left), Inches(3.55), width=w)
        placed += 1

    note = "Snapshots (L\u2192R, top\u2192bottom): " + " \u00b7 ".join(
        captions.get(s.stem, s.stem) for s in shots
    )
    box = slide.shapes.add_textbox(Inches(0.25), Inches(5.32), Inches(9.5), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = note
    run.font.size = Pt(8)
    run.font.color.rgb = DARK
    return placed


def main() -> None:
    if not TEMPLATE.is_file():
        raise SystemExit(f"Template not found: {TEMPLATE}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation(str(TEMPLATE))
    slides = list(prs.slides)

    fill_slide1(slides[0])
    for idx, items in BODIES.items():
        # Slide 9 is dense -> smaller font / taller box.
        if idx == 9:
            add_body(slides[idx - 1], items, top=1.55, height=3.9, font=11)
        elif idx in (3, 4, 5, 7):
            add_body(slides[idx - 1], items, top=1.7, height=3.7, font=12)
        else:
            add_body(slides[idx - 1], items, top=1.6, height=3.8, font=13)
    placed = fill_snapshots(slides[10])  # slide 11

    prs.save(str(OUT))
    print(f"Saved {OUT}")
    print(f"  screenshots placed on slide 11: {placed}")


if __name__ == "__main__":
    main()
