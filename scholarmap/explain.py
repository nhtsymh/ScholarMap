from __future__ import annotations
from .models import Paper


def why_it_matters(p: Paper, section: str) -> str:
    # Grounded template for V0.2; avoids hallucinating scientific claims.
    bits = []
    if section == "top_conference" and p.venue:
        bits.append(f"Published at {p.venue}")
    if section == "most_cited":
        bits.append(f"has {p.cited_by_count} citations in the selected research landscape")
    if section == "open_source" and p.repositories:
        best = max(p.repositories, key=lambda r: r.stars or 0)
        bits.append(f"has {'official ' if best.official else ''}open-source code" + (f" with {best.stars:,} GitHub stars" if best.stars is not None else ""))
    if section == "classics":
        bits.append("ranks highly on query-conditioned foundationality")
    if section == "strong_labs":
        bits.append("comes from a topic-leading institution identified from prior work")
    if section == "surveys":
        bits.append("is identified as a survey/review and is directly relevant to the topic")
    if not bits:
        return "Ranked highly for relevance and impact in this query."
    text = "; ".join(bits)
    return text[:1].upper() + text[1:] + "."
