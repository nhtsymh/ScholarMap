from __future__ import annotations
from datetime import date
import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Paper
from ..utils import months_between, minmax


def textual_relevance(query: str, papers: list[Paper]) -> dict[str, float]:
    if not papers: return {}
    texts = [query] + [f"{p.title}. {p.abstract}" for p in papers]
    try:
        X = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000).fit_transform(texts)
        sims = cosine_similarity(X[0:1], X[1:]).ravel()
    except ValueError:
        sims = np.zeros(len(papers))
    return {p.id: float(s) for p, s in zip(papers, sims)}


def age_normalized_impact(paper: Paper, as_of: date) -> float:
    months = months_between(paper.publication_date, as_of)
    return math.log1p(max(0, paper.cited_by_count)) / math.sqrt(months)


def impact_percentiles(papers: list[Paper], as_of: date) -> dict[str, float]:
    # Topic-age cohorts: compare papers in +/- 6 month age bins within the current query result.
    out = {}
    for p in papers:
        age = months_between(p.publication_date, as_of)
        cohort = [q for q in papers if abs(months_between(q.publication_date, as_of) - age) <= 6]
        vals = sorted(q.cited_by_count for q in cohort)
        if not vals:
            out[p.id] = 0.0; continue
        less_eq = sum(v <= p.cited_by_count for v in vals)
        out[p.id] = round(100.0 * less_eq / len(vals), 1)
    return out
