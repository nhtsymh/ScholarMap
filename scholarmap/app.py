from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from .models import SearchRequest, SearchResponse, AuthorPapersRequest, AuthorPapersResponse
from .service import ScholarMapService

BASE=Path(__file__).parent
app=FastAPI(
    title="ScholarMap",
    version="0.2.0",
    description="Query-conditioned scholarly discovery and research landscape ranking.",
)
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static")
service=ScholarMapService()


@app.get("/")
async def index():
    return FileResponse(BASE/"static"/"index.html")


@app.get("/health")
async def health():
    return {"status":"ok","name":"ScholarMap","version":"0.2.0"}


@app.post("/api/search",response_model=SearchResponse)
async def search(req:SearchRequest):
    try:
        return await service.search(req)
    except ValueError as e:
        raise HTTPException(400,str(e))


@app.post("/api/authors/papers",response_model=AuthorPapersResponse)
async def author_papers(req: AuthorPapersRequest):
    try:
        return await service.author_papers(req)
    except ValueError as e:
        raise HTTPException(400,str(e))


@app.get("/api/paper/{paper_id}")
async def paper(paper_id: str):
    item = service.paper_cache.get(paper_id)
    if not item:
        raise HTTPException(404, "paper not found in the latest search cache")
    return item.model_dump(mode="json")


@app.get("/api/evidence/{paper_id}")
async def evidence(paper_id: str):
    item = service.paper_cache.get(paper_id)
    if not item:
        raise HTTPException(404, "paper not found in the latest search cache")
    return {"paper_id": paper_id, "title": item.title, "evidence": [e.model_dump(mode="json") for e in item.evidence]}


@app.post("/api/export/bibtex",response_class=PlainTextResponse)
async def export_bibtex(payload:dict):
    papers=payload.get("papers",[])
    blocks=[]
    for i,p in enumerate(papers):
        title=str(p.get("title","")).replace("{","").replace("}","")
        raw_authors=p.get("authors",[])
        authors=" and ".join(a.get("name","") if isinstance(a,dict) else str(a) for a in raw_authors)
        year=str(p.get("publication_date",""))[:4]
        venue=p.get("venue") or ""
        key=f"scholarmap{i+1}"
        blocks.append(f"@article{{{key},\n  title={{{title}}},\n  author={{{authors}}},\n  year={{{year}}},\n  journal={{{venue}}}\n}}")
    return "\n\n".join(blocks)
