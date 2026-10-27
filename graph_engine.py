"""Criminal network analysis with NetworkX.

Builds a co-accused graph (accused persons linked when they appear together on a
case), then computes:
  * community detection (greedy modularity) -> suspected gangs/clusters
  * degree + betweenness centrality -> kingpins / bridge figures
  * repeat-offender ranking by distinct case count

Every accused node carries a presumption-of-innocence flag: accused != convicted.
Respects RBAC scope (only cases within scope contribute edges).
"""
from __future__ import annotations

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from ..db import query
from ..rbac import User, scope_where


def _load_edges(user: User):
    clause, params = scope_where(user, "cm")
    rows = query(
        "SELECT a.CaseMasterID, a.AccusedMasterID, am.Name "
        "FROM Accused a "
        "JOIN AccusedMaster am ON a.AccusedMasterID = am.AccusedMasterID "
        "JOIN CaseMaster cm ON a.CaseMasterID = cm.CaseMasterID "
        "WHERE 1=1" + clause,
        tuple(params),
    )
    return rows


def build_graph(user: User) -> tuple[nx.Graph, dict]:
    rows = _load_edges(user)
    by_case: dict[int, list[int]] = {}
    names: dict[int, str] = {}
    case_count: dict[int, int] = {}
    for r in rows:
        by_case.setdefault(r["CaseMasterID"], []).append(r["AccusedMasterID"])
        names[r["AccusedMasterID"]] = r["Name"]
        case_count[r["AccusedMasterID"]] = case_count.get(r["AccusedMasterID"], 0) + 1

    G = nx.Graph()
    for amid, name in names.items():
        G.add_node(amid, name=name, cases=case_count[amid])
    for case_id, members in by_case.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    return G, case_count


def analyze(user: User, min_community: int = 3, top: int = 10) -> dict:
    G, case_count = build_graph(user)
    if G.number_of_nodes() == 0:
        return {"answer": "No co-accused network data in your scope.",
                "nodes": [], "edges": [], "communities": [], "kingpins": [],
                "repeat_offenders": [], "module": "Graph engine"}

    # Centrality (on the largest pieces; betweenness can be heavy, sample if huge)
    deg = dict(G.degree())
    try:
        btw = nx.betweenness_centrality(G, k=min(30, G.number_of_nodes()), seed=42)
    except Exception:
        btw = {n: 0.0 for n in G.nodes()}

    # Communities
    communities = []
    try:
        comms = greedy_modularity_communities(G, weight="weight")
        for idx, c in enumerate(comms):
            members = sorted(c, key=lambda n: deg.get(n, 0), reverse=True)
            if len(members) >= min_community:
                communities.append({
                    "id": idx,
                    "size": len(members),
                    "members": [{"id": n, "name": G.nodes[n]["name"],
                                 "cases": G.nodes[n]["cases"]} for n in members[:12]],
                })
    except Exception:
        pass
    communities.sort(key=lambda c: c["size"], reverse=True)

    kingpins = sorted(
        ({"id": n, "name": G.nodes[n]["name"], "degree": deg[n],
          "betweenness": round(btw.get(n, 0.0), 4), "cases": G.nodes[n]["cases"]}
         for n in G.nodes()),
        key=lambda x: (x["betweenness"], x["degree"]), reverse=True,
    )[:top]

    repeat = sorted(
        ({"id": amid, "name": G.nodes[amid]["name"], "cases": cnt}
         for amid, cnt in case_count.items() if cnt > 1),
        key=lambda x: x["cases"], reverse=True,
    )[:top]

    # Export a trimmed graph for visualization (largest community + kingpins)
    keep = set()
    for c in communities[:3]:
        keep.update(m["id"] for m in c["members"])
    keep.update(k["id"] for k in kingpins)
    sub = G.subgraph(keep)
    nodes = [{"id": n, "label": G.nodes[n]["name"], "cases": G.nodes[n]["cases"],
              "presumption": "Accused - not convicted"} for n in sub.nodes()]
    edges = [{"from": u, "to": v, "weight": d["weight"]}
             for u, v, d in sub.edges(data=True)]

    answer = (f"Network has {G.number_of_nodes()} accused persons and "
              f"{G.number_of_edges()} co-accused links. Detected {len(communities)} "
              f"cluster(s); top suspected kingpin: {kingpins[0]['name']} "
              f"(degree {kingpins[0]['degree']}).")
    return {
        "answer": answer,
        "nodes": nodes,
        "edges": edges,
        "communities": communities[:5],
        "kingpins": kingpins,
        "repeat_offenders": repeat,
        "disclaimer": "All individuals shown are ACCUSED, not convicted. "
                      "Presumption of innocence applies.",
        "module": "Graph engine",
    }
