import httpx, pytest
from datetime import date
from scholarmap.providers.openalex import OpenAlexProvider
from scholarmap.providers.arxiv import ArxivProvider

@pytest.mark.asyncio
async def test_openalex_query_contract():
    seen={}
    def handler(req):
        seen['url']=str(req.url)
        return httpx.Response(200,json={"results":[]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        p=OpenAlexProvider(client=client,api_key="KEY")
        await p.search("llm agents",date(2025,1,1),date(2025,2,28),limit=42,sort="cited_by_count:desc")
    assert 'search=llm+agents' in seen['url']
    assert 'per_page=42' in seen['url']
    assert 'from_publication_date%3A2025-01-01' in seen['url']
    assert 'to_publication_date%3A2025-02-28' in seen['url']
    assert 'sort=cited_by_count%3Adesc' in seen['url']
    assert 'api_key=KEY' in seen['url']

@pytest.mark.asyncio
async def test_arxiv_query_contract():
    atom='<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    seen={}
    def handler(req):
        seen['url']=str(req.url)
        return httpx.Response(200,text=atom)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        p=ArxivProvider(client=client)
        out=await p.search("llm agents",date(2025,1,1),date(2025,1,31),limit=7)
    assert out==[]
    assert 'max_results=7' in seen['url']
    assert 'submittedDate' in seen['url']
