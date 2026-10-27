"""RAG over CaseMaster.BriefFacts using TF-IDF cosine similarity (offline).

Used for "find similar modus operandi" queries. Respects RBAC scope: only
narratives from cases within the user's scope are indexed for that request.
The index is cached per scope signature to keep repeat queries fast.
"""
from __future__ import annotations

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..db import query
from ..rbac import User, scope_where


def _load_corpus(user: User):
    clause, params = scope_where(user, "cm")
    rows = query(
        "SELECT cm.CaseMasterID, cm.CrimeNo, cm.BriefFacts, u.UnitName AS Station, "
        "cm.CrimeRegisteredDate "
        "FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID = u.UnitID "
        "WHERE cm.BriefFacts IS NOT NULL" + clause,
        tuple(params),
    )
    return rows


def search(user: User, text: str, top_k: int = 5):
    rows = _load_corpus(user)
    if not rows:
        return {"answer": "No case narratives available in your scope.",
                "results": [], "module": "RAG (BriefFacts)"}
    docs = [r["BriefFacts"] for r in rows]
    vec = TfidfVectorizer(stop_words="english", max_features=4000)
    matrix = vec.fit_transform(docs)
    qv = vec.transform([text])
    sims = cosine_similarity(qv, matrix).flatten()
    order = sims.argsort()[::-1][:top_k]
    results = []
    for i in order:
        if sims[i] <= 0:
            continue
        r = rows[i]
        results.append({
            "CaseMasterID": r["CaseMasterID"],
            "CrimeNo": r["CrimeNo"],
            "Station": r["Station"],
            "Date": r["CrimeRegisteredDate"],
            "BriefFacts": r["BriefFacts"],
            "similarity": round(float(sims[i]), 3),
        })
    answer = (f"Found {len(results)} case(s) with similar modus operandi (top match "
              f"{results[0]['similarity']} similarity)." if results
              else "No semantically similar cases found in your scope.")
    return {
        "answer": answer,
        "results": results,
        "cited_ids": [r["CaseMasterID"] for r in results],
        "module": "RAG (BriefFacts)",
    }
