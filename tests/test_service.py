import pytest
from scholarmap.models import SearchRequest
from scholarmap.service import ScholarMapService

@pytest.mark.asyncio
async def test_demo_search_all_sections():
    req=SearchRequest(topic="continual learning for large language models",date_from="2025-01",date_to="2026-07",live=False,papers_per_section=5)
    res=await ScholarMapService().search(req)
    assert res.candidate_count>0
    keys={s.key for s in res.sections}
    assert keys=={"top_conference","strong_labs","most_cited","surveys","classics","open_source"}
    assert any("Demo mode" in w for w in res.warnings)

@pytest.mark.asyncio
async def test_most_cited_descending():
    req=SearchRequest(topic="continual learning",date_from="2025-01",date_to="2026-07",sections=["most_cited"],live=False,papers_per_section=20)
    res=await ScholarMapService().search(req)
    vals=[p.citations for p in res.sections[0].papers]
    assert vals==sorted(vals,reverse=True)

@pytest.mark.asyncio
async def test_date_filter_excludes_classic_from_target_count():
    req=SearchRequest(topic="continual learning",date_from="2026-01",date_to="2026-07",sections=["most_cited","classics"],live=False,papers_per_section=20)
    res=await ScholarMapService().search(req)
    target=res.sections[0].papers
    assert all(str(p.publication_date).startswith("2026-") for p in target)
    classics=res.sections[1].papers
    assert any(p.publication_date and p.publication_date.year < 2026 for p in classics)

@pytest.mark.asyncio
async def test_top_conference_filter():
    req=SearchRequest(topic="continual learning",date_from="2025-01",date_to="2026-07",sections=["top_conference"],live=False,papers_per_section=20)
    res=await ScholarMapService().search(req)
    assert res.sections[0].papers
    assert all(p.venue in {"ICLR","ICML","NeurIPS"} for p in res.sections[0].papers)
