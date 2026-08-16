import httpx, pytest
from scholarmap.providers.github import GitHubProvider
from scholarmap.providers.crossref import CrossrefProvider
from scholarmap.providers.dblp import DBLPProvider
from scholarmap.providers.openreview import OpenReviewProvider

@pytest.mark.asyncio
async def test_github_repository_lookup():
    def handler(req):
        return httpx.Response(200,json={"items":[{"name":"continual-learning-llms","description":"Continual Learning for Large Language Models 2501.12345","html_url":"https://github.com/x/y","stargazers_count":321}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        repo=await GitHubProvider(client=c).find_repository("Continual Learning for Large Language Models","2501.12345")
    assert repo and repo.stars==321 and repo.url.endswith('/x/y')

@pytest.mark.asyncio
async def test_crossref_lookup():
    def handler(req): return httpx.Response(200,json={"message":{"items":[{"DOI":"10.1/x","title":["X"]}]}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        x=await CrossrefProvider(client=c).lookup_title("X")
    assert x['DOI']=='10.1/x'

@pytest.mark.asyncio
async def test_dblp_lookup():
    def handler(req): return httpx.Response(200,json={"result":{"hits":{"hit":[{"info":{"title":"X"}}]}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        hits=await DBLPProvider(client=c).search_title("X")
    assert hits[0]['info']['title']=='X'

@pytest.mark.asyncio
async def test_openreview_notes():
    def handler(req): return httpx.Response(200,json={"notes":[{"id":"n1"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        notes=await OpenReviewProvider(client=c).get_notes("ICLR.cc/2026/Conference/-/Submission")
    assert notes==[{"id":"n1"}]
