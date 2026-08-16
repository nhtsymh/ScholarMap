from __future__ import annotations
import httpx
import pytest
from fastapi.testclient import TestClient
from scholarmap.app import app
from scholarmap.models import AuthorPapersRequest
from scholarmap.providers.openalex import OpenAlexProvider
from scholarmap.service import ScholarMapService


def test_search_cards_expose_clickable_author_identity():
    client=TestClient(app)
    r=client.post('/api/search',json={
        'topic':'continual learning',
        'date_from':'2025-01',
        'date_to':'2026-07',
        'live':False,
        'sections':['most_cited'],
    })
    assert r.status_code==200
    card=r.json()['sections'][0]['papers'][0]
    assert card['author_details']
    assert card['author_details'][0]['name']
    assert card['author_details'][0]['id']


def test_author_explorer_demo_returns_all_time_topic_papers():
    client=TestClient(app)
    r=client.post('/api/authors/papers',json={
        'author_id':'A-DEMO-MAYA',
        'author_name':'Maya Chen',
        'topic':'continual learning',
        'live':False,
        'limit':1000,
    })
    assert r.status_code==200
    data=r.json()
    assert data['author']['name']=='Maya Chen'
    assert data['paper_count'] >= 4
    years={p['publication_date'][:4] for p in data['papers'] if p['publication_date']}
    assert '2018' in years and '2026' in years
    assert all('Maya Chen' in p['authors'] for p in data['papers'])


def test_frontend_contains_author_explorer_hooks():
    client=TestClient(app)
    html=client.get('/').text
    js=client.get('/static/app.js').text
    assert 'AUTHOR EXPLORER' in html
    assert '/api/authors/papers' in js
    assert 'author-link' in js


@pytest.mark.asyncio
async def test_openalex_author_resolution_and_exact_id_filter_contract():
    seen=[]
    def handler(req: httpx.Request):
        seen.append(str(req.url))
        if '/authors?' in str(req.url):
            return httpx.Response(200,json={
                'results':[
                    {'id':'https://openalex.org/A123','display_name':'Maya Chen'},
                    {'id':'https://openalex.org/A999','display_name':'Maya J. Chen'},
                ]
            })
        return httpx.Response(200,json={
            'meta':{'count':1,'next_cursor':None},
            'results':[{
                'id':'https://openalex.org/W1',
                'display_name':'Continual Learning Paper',
                'publication_date':'2025-01-01',
                'cited_by_count':4,
                'authorships':[{
                    'author':{'id':'https://openalex.org/A123','display_name':'Maya Chen'},
                    'institutions':[]
                }],
                'referenced_works':[],
                'ids':{},
                'primary_location':{}
            }]
        })
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider=OpenAlexProvider(client=client)
        author=await provider.resolve_author('Maya Chen')
        papers,total=await provider.author_works(author.id,'continual learning',limit=1000)
    assert author.id=='A123'
    assert total==1 and papers[0].authors[0].id=='A123'
    work_url=next(u for u in seen if '/works?' in u)
    assert 'authorships.author.id%3AA123' in work_url
    assert 'search=continual+learning' in work_url
    assert 'cursor=%2A' in work_url


class LiveAuthorOpenAlex:
    async def resolve_author(self,name):
        raise AssertionError('stable ID should avoid name resolution')

    async def author_works(self,author_id,query,limit=1000):
        from datetime import date
        from scholarmap.models import Paper, Author
        assert author_id=='A123'
        assert query=='continual learning'
        return [Paper(
            id='W1',title='Continual Learning by Author',abstract='continual learning',
            publication_date=date(2025,1,1),authors=[Author(name='Maya Chen',id='A123')],
            cited_by_count=10,
        )],1


@pytest.mark.asyncio
async def test_live_author_explorer_uses_stable_author_id():
    svc=ScholarMapService(openalex=LiveAuthorOpenAlex())
    res=await svc.author_papers(AuthorPapersRequest(
        author_id='A123',author_name='Maya Chen',topic='continual learning',live=True,limit=1000
    ))
    assert res.paper_count==1
    assert res.papers[0].author_details[0].id=='A123'
    assert not any('resolved by name' in w for w in res.warnings)


def test_paper_endpoint_after_search():
    client=TestClient(app)
    r=client.post('/api/search',json={
        'topic':'continual learning','date_from':'2025-01','date_to':'2026-07','live':False,
        'sections':['most_cited']
    })
    pid=r.json()['sections'][0]['papers'][0]['id']
    p=client.get(f'/api/paper/{pid}')
    assert p.status_code==200
    assert p.json()['id']==pid


def test_missing_paper_endpoint_is_404():
    client=TestClient(app)
    assert client.get('/api/paper/NOT-HERE').status_code==404


class NameResolvingOpenAlex:
    async def resolve_author(self,name):
        from scholarmap.models import Author
        assert name=='Name Only'
        return Author(name='Name Only',id='A777')

    async def author_works(self,author_id,query,limit=1000):
        assert author_id=='A777'
        return [],0


@pytest.mark.asyncio
async def test_live_author_explorer_resolves_missing_id_by_name():
    svc=ScholarMapService(openalex=NameResolvingOpenAlex())
    res=await svc.author_papers(AuthorPapersRequest(
        author_name='Name Only',topic='continual learning',live=True,limit=100
    ))
    assert res.author.id=='A777'
    assert any('resolved by name' in w for w in res.warnings)
