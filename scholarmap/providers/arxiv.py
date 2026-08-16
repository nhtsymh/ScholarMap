from __future__ import annotations
from datetime import date
import re
import xml.etree.ElementTree as ET
import httpx
from .base import PaperProvider
from ..models import Paper, Author, Evidence

ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivProvider(PaperProvider):
    name = "arxiv"
    base_url = "https://export.arxiv.org/api/query"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def search(self, query: str, date_from: date | None = None, date_to: date | None = None,
                     limit: int = 100, sort: str | None = None) -> list[Paper]:
        q = f'all:"{query}"'
        if date_from or date_to:
            start = (date_from or date(1991, 1, 1)).strftime("%Y%m%d0000")
            end = (date_to or date.today()).strftime("%Y%m%d2359")
            q += f" AND submittedDate:[{start} TO {end}]"
        params = {"search_query": q, "start": 0, "max_results": min(limit, 100),
                  "sortBy": "submittedDate", "sortOrder": "descending"}
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=20, headers={"User-Agent": "ScholarMap/0.2"})
        try:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
            return self.parse_atom(r.text)
        finally:
            if owns:
                await client.aclose()

    @staticmethod
    def parse_atom(text: str) -> list[Paper]:
        root = ET.fromstring(text)
        out = []
        for e in root.findall("a:entry", ATOM):
            raw_id = (e.findtext("a:id", default="", namespaces=ATOM) or "").split("/abs/")[-1]
            arxiv_id = re.sub(r"v\d+$", "", raw_id)
            title = " ".join((e.findtext("a:title", default="", namespaces=ATOM) or "").split())
            abstract = " ".join((e.findtext("a:summary", default="", namespaces=ATOM) or "").split())
            published = e.findtext("a:published", default="", namespaces=ATOM)
            pub_date = date.fromisoformat(published[:10]) if published else None
            authors = [Author(name=a.findtext("a:name", default="", namespaces=ATOM)) for a in e.findall("a:author", ATOM)]
            pdf = None
            for link in e.findall("a:link", ATOM):
                if link.attrib.get("title") == "pdf":
                    pdf = link.attrib.get("href")
            doi = e.findtext("arxiv:doi", default=None, namespaces=ATOM)
            out.append(Paper(
                id=f"arxiv:{arxiv_id}", title=title, abstract=abstract, publication_date=pub_date,
                authors=authors, doi=doi, arxiv_id=arxiv_id,
                primary_url=f"https://arxiv.org/abs/{arxiv_id}", pdf_url=pdf,
                source_records=["arXiv"],
                evidence=[Evidence(field="arxiv_id", value=arxiv_id, source="arXiv", confidence=1.0)]
            ))
        return out
