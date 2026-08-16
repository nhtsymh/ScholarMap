from __future__ import annotations
from collections import defaultdict
from datetime import date
import math
from .common import textual_relevance, age_normalized_impact
from ..models import Paper


def lab_rank(query: str, historical_papers: list[Paper], cutoff: date,
             venue_signal: callable | None = None) -> dict[str, float]:
    """Topic-conditioned institution strength using ONLY papers before cutoff."""
    eligible = [p for p in historical_papers if p.publication_date and p.publication_date < cutoff]
    rel = textual_relevance(query, eligible)
    raw = defaultdict(float)
    for p in eligible:
        years_old = max(0, (cutoff - p.publication_date).days / 365.25)
        decay = math.exp(-0.18 * years_old)
        impact = age_normalized_impact(p, cutoff)
        venue = float(venue_signal(p.venue) if venue_signal else 1.0)
        insts = p.institutions
        if not insts: continue
        contribution = rel.get(p.id, 0) * (1 + impact) * venue * decay / len(insts)
        for inst in insts:
            raw[inst] += contribution
    if not raw: return {}
    hi = max(raw.values()) or 1
    return {k: v / hi for k, v in raw.items()}
