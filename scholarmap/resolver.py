from __future__ import annotations
from difflib import SequenceMatcher
from .models import Paper
from .utils import normalize_title


def _clean_doi(doi: str | None) -> str | None:
    if not doi: return None
    return doi.lower().replace("https://doi.org/", "").replace("http://doi.org/", "").strip()


def same_paper(a: Paper, b: Paper) -> bool:
    da, db = _clean_doi(a.doi), _clean_doi(b.doi)
    if da and db and da == db: return True
    if a.arxiv_id and b.arxiv_id and a.arxiv_id == b.arxiv_id: return True
    ta, tb = normalize_title(a.title), normalize_title(b.title)
    if ta == tb and ta: return True
    ratio = SequenceMatcher(None, ta, tb).ratio()
    toks_a, toks_b = set(ta.split()), set(tb.split())
    containment = bool(toks_a and toks_b and (toks_a <= toks_b or toks_b <= toks_a))
    jaccard = len(toks_a & toks_b) / max(1, len(toks_a | toks_b))
    aa = {x.name.lower() for x in a.authors}
    ab = {x.name.lower() for x in b.authors}
    overlap = len(aa & ab) / max(1, min(len(aa), len(ab))) if aa and ab else 0
    # Conference versions often append subtitles to arXiv titles. Require either
    # very strong title similarity, or strong token containment plus author evidence.
    return ratio >= 0.94 or (containment and jaccard >= 0.60 and overlap >= 0.5) or (ratio >= 0.88 and overlap >= 0.5)


def merge_papers(a: Paper, b: Paper) -> Paper:
    # Prefer richer/verified fields while preserving all evidence/provenance.
    a.title = a.title if len(a.title) >= len(b.title) else b.title
    if len(b.abstract) > len(a.abstract): a.abstract = b.abstract
    a.publication_date = a.publication_date or b.publication_date
    a.venue = a.venue or b.venue
    a.venue_id = a.venue_id or b.venue_id
    a.publication_status = a.publication_status or b.publication_status
    by_name = {x.name.lower(): x for x in a.authors}
    for au in b.authors:
        by_name.setdefault(au.name.lower(), au)
    a.authors = list(by_name.values())
    a.institutions = sorted(set(a.institutions) | set(b.institutions))
    a.cited_by_count = max(a.cited_by_count, b.cited_by_count)
    a.referenced_works = sorted(set(a.referenced_works) | set(b.referenced_works))
    a.doi = a.doi or b.doi
    a.arxiv_id = a.arxiv_id or b.arxiv_id
    a.external_ids.update(b.external_ids)
    a.primary_url = a.primary_url or b.primary_url
    a.pdf_url = a.pdf_url or b.pdf_url
    a.repositories.extend(r for r in b.repositories if r.url not in {x.url for x in a.repositories})
    a.evidence.extend(b.evidence)
    a.source_records = sorted(set(a.source_records) | set(b.source_records))
    return a


def canonicalize(papers: list[Paper]) -> list[Paper]:
    out: list[Paper] = []
    for p in papers:
        found = None
        for i, existing in enumerate(out):
            if same_paper(existing, p):
                found = i; break
        if found is None:
            out.append(p.model_copy(deep=True))
        else:
            out[found] = merge_papers(out[found], p)
    return out
