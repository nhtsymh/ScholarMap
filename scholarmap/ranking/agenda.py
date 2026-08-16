from __future__ import annotations
import networkx as nx
from .common import textual_relevance
from ..models import Paper
from ..utils import minmax


def agenda_rank(query: str, papers: list[Paper]) -> dict[str, float]:
    """Combine text relevance, local citation-community alignment and graph centrality."""
    if not papers: return {}
    rel = textual_relevance(query, papers)
    ids = {p.id for p in papers}
    g = nx.DiGraph()
    g.add_nodes_from(ids)
    for p in papers:
        for ref in p.referenced_works:
            if ref in ids:
                g.add_edge(p.id, ref)
    ug = g.to_undirected()
    communities = []
    if ug.number_of_edges() > 0:
        try:
            communities = list(nx.community.greedy_modularity_communities(ug))
        except Exception:
            communities = []
    if not communities:
        communities = [{p.id} for p in papers]
    community_alignment: dict[str, float] = {}
    for c in communities:
        vals = [rel.get(pid, 0.0) for pid in c]
        alignment = sum(vals) / max(1, len(vals))
        for pid in c: community_alignment[pid] = alignment
    if g.number_of_edges() > 0:
        centrality = nx.pagerank(g.reverse(), alpha=0.85)
    else:
        centrality = {pid: 0.0 for pid in ids}
    centr_norm_vals = minmax([centrality.get(p.id, 0) for p in papers])
    scores = {}
    for p, cn in zip(papers, centr_norm_vals):
        scores[p.id] = 0.65 * rel.get(p.id, 0) + 0.25 * community_alignment.get(p.id, 0) + 0.10 * cn
    return scores
