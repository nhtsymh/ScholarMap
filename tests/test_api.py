from fastapi.testclient import TestClient
from scholarmap.app import app

client=TestClient(app)

def test_health():
    r=client.get('/health')
    assert r.status_code==200 and r.json()['status']=='ok'

def test_index():
    r=client.get('/')
    assert r.status_code==200
    assert 'ScholarMap' in r.text

def test_search_api():
    r=client.post('/api/search',json={"topic":"continual learning","date_from":"2025-01","date_to":"2026-07","live":False})
    assert r.status_code==200
    data=r.json()
    assert len(data['sections'])==6

def test_bibtex_export():
    r=client.post('/api/export/bibtex',json={"papers":[{"title":"Paper A","authors":["Alice","Bob"],"publication_date":"2025-01-01","venue":"ICLR"}]})
    assert r.status_code==200
    assert '@article{scholarmap1' in r.text
    assert 'Alice and Bob' in r.text

def test_bad_date_range_is_400():
    r=client.post('/api/search',json={"topic":"continual learning","date_from":"2026-07","date_to":"2025-01","live":False})
    assert r.status_code==400

def test_evidence_endpoint_after_search():
    r=client.post('/api/search',json={"topic":"continual learning","date_from":"2025-01","date_to":"2026-07","live":False,"sections":["most_cited"]})
    pid=r.json()['sections'][0]['papers'][0]['id']
    e=client.get(f'/api/evidence/{pid}')
    assert e.status_code==200
    assert e.json()['evidence']

def test_missing_evidence_is_404():
    r=client.get('/api/evidence/DOES_NOT_EXIST')
    assert r.status_code==404
