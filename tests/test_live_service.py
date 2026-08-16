from datetime import date
import pytest
from scholarmap.models import Paper, Repository, SearchRequest
from scholarmap.service import ScholarMapService

class FakeOpenAlex:
    async def search(self, query, date_from=None, date_to=None, limit=100, sort=None):
        if sort:
            return [Paper(id='old',title='continual learning foundation',abstract='continual learning',publication_date=date(2020,1,1),cited_by_count=500,institutions=['Lab A'])]
        if date_from and date_from.year <= 2020:
            return [Paper(id='hist',title='continual learning prior work',abstract='continual learning',publication_date=date(2024,1,1),cited_by_count=50,institutions=['Lab A'])]
        return [Paper(id='new',title='continual learning new work',abstract='continual learning',publication_date=date(2026,2,1),venue='ICLR',cited_by_count=10,institutions=['Lab A'])]

class FakeArxiv:
    async def search(self,*args,**kwargs): return []

class FakeGithub:
    async def find_repository(self,title,arxiv_id=None): return Repository(url='https://github.com/x/y',stars=10,official=True,confidence=1)

@pytest.mark.asyncio
async def test_live_path_with_injected_providers():
    svc=ScholarMapService(FakeOpenAlex(),FakeArxiv(),FakeGithub())
    req=SearchRequest(topic='continual learning',date_from='2026-01',date_to='2026-07',live=True,papers_per_section=5)
    res=await svc.search(req)
    assert not any('Live providers failed' in w for w in res.warnings)
    assert res.candidate_count==1
    open_sec=next(s for s in res.sections if s.key=='open_source')
    assert open_sec.papers[0].repositories[0].stars==10
    strong=next(s for s in res.sections if s.key=='strong_labs')
    assert strong.papers and 'Lab A' in strong.papers[0].institutions
