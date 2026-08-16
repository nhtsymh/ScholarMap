from __future__ import annotations
from collections import defaultdict
import networkx as nx
from .common import textual_relevance, age_normalized_impact
from ..models import Paper
from ..utils import minmax
from datetime import date


def foundation_rank(query: str, papers: list[Paper], as_of: date) -> dict[str, float]:
    if not papers: return {}
    ids = {p.id for p in papers}
    g = nx.DiGraph()
    g.add_nodes_from(ids)
    for p in papers:
        for ref in p.referenced_works:
            if ref in ids:
                # citing -> cited
                g.add_edge(p.id, ref)
    rel = textual_relevance(query, papers)
    total_rel = sum(rel.values())
    personalization = {pid: (rel.get(pid, 0) / total_rel if total_rel > 0 else 1/len(ids)) for pid in ids}
    if g.number_of_edges() > 0:
        # Citation edges are citing -> cited, so PageRank on the original graph rewards
        # works repeatedly reached through relevant descendants (a natural foundationality signal).
        ppr = nx.pagerank(g, alpha=0.85, personalization=personalization)
        ug = g.to_undirected()
        try:
            comms = list(nx.community.greedy_modularity_communities(ug))
        except Exception:
            comms = [{pid} for pid in ids]
    else:
        ppr = {pid: personalization[pid] for pid in ids}
        comms = [{pid} for pid in ids]
    comm_of = {}
    for i, c in enumerate(comms):
        for pid in c: comm_of[pid] = i
    breadth = {}
    rg = g.reverse()
    for pid in ids:
        communities_seen = set()
        direct_branches = 0
        if g.number_of_edges() > 0:
            direct_branches = rg.out_degree(pid)
            lengths = nx.single_source_shortest_path_length(rg, pid, cutoff=3)
            for d in lengths:
                if d != pid:
                    communities_seen.add(comm_of.get(d, -1))
        # A foundational work should seed multiple downstream branches, not merely
        # sit on a single highly-cited chain. Direct independent citers are a robust
        # local proxy when community detection is coarse on small query graphs.
        breadth[pid] = direct_branches + 0.75 * len(communities_seen)
    ppr_n = minmax([ppr.get(p.id, 0) for p in papers])
    br_n = minmax([breadth.get(p.id, 0) for p in papers])
    im_n = minmax([age_normalized_impact(p, as_of) for p in papers])
    return {p.id: 0.45*a + 0.35*b + 0.20*c for p, a, b, c in zip(papers, ppr_n, br_n, im_n)}
