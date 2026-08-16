from __future__ import annotations
import math
from datetime import date
from ..models import Paper
from ..config import AI_ML_VENUES
from ..utils import canonical_venue, minmax
from .common import age_normalized_impact


def venue_score(name: str | None) -> float:
    c = canonical_venue(name)
    return 1.0 if c in AI_ML_VENUES else 0.25


def recommended_scores(papers: list[Paper], agenda: dict[str, float], as_of: date) -> dict[str, float]:
    impacts = minmax([age_normalized_impact(p, as_of) for p in papers])
    citations = minmax([math.log1p(p.cited_by_count) for p in papers])
    out = {}
    for p, im, cit in zip(papers, impacts, citations):
        open_signal = 1.0 if p.repositories else 0.0
        out[p.id] = 0.5*agenda.get(p.id, 0) + 0.18*cit + 0.15*im + 0.12*venue_score(p.venue) + 0.05*open_signal
    return out
