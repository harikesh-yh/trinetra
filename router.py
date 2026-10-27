"""Router agent: reads a natural-language question, selects the right engine
module, runs it, and composes a trustworthy answer (cited + confidence/caveat).

Routing is keyword/intent based (offline). Every routed call is audit-logged by
the API layer. The router attaches a confidence + sample-size caveat to results.
"""
from __future__ import annotations

from . import rag, text2sql
from ..rbac import User


def _confidence(n: int) -> dict:
    """Crude confidence band from sample size, with a caveat string."""
    if n == 0:
        return {"level": "none", "caveat": "No matching records - cannot draw conclusions."}
    if n < 10:
        return {"level": "low",
                "caveat": f"Low sample size (n={n}); treat as indicative only."}
    if n < 50:
        return {"level": "medium", "caveat": f"Moderate sample size (n={n})."}
    return {"level": "high", "caveat": f"Sample size n={n}."}


def route(user: User, question: str) -> dict:
    ql = question.lower()

    # Similar-MO / narrative search -> RAG
    if any(k in ql for k in ("similar", "modus operandi", "same mo", "like this",
                             "matching cases", "resembl")):
        res = rag.search(user, question)
        n = len(res.get("results", []))
        res["confidence"] = _confidence(n)
        res["route"] = "RAG"
        return res

    # Default analytics path -> Text->SQL
    result = text2sql.run(user, question)
    out = result.to_dict()
    n = len(out["rows"])
    out["confidence"] = _confidence(n)
    out["route"] = "Text->SQL"
    return out
