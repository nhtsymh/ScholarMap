from __future__ import annotations
from datetime import date
import os
import httpx
from .base import PaperProvider
from ..models import Paper, Author, Evidence
from ..utils import canonical_venue


def _invert_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words = []
    for word, positions in index.items():
        for pos in positions:
            words.append((pos, word))
    return " ".join(w for _, w in sorted(words))


def _openalex_tail(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip("/").split("/")[-1]


class OpenAlexProvider(PaperProvider):
    name = "openalex"
    base_url = "https://api.openalex.org/works"
    authors_url = "https://api.openalex.org/authors"

    def __init__(self, client: httpx.AsyncClient | None = None, mailto: str | None = None, api_key: str | None = None):
        self.client = client
        self.mailto = mailto
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY")

    def _auth_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.mailto:
            params["mailto"] = self.mailto
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    async def search(self, query: str, date_from: date | None = None, date_to: date | None = None,
                     limit: int = 100, sort: str | None = None) -> list[Paper]:
        params: dict[str, str | int] = {"search": query, "per_page": min(limit, 100), **self._auth_params()}
        filters = []
        if date_from:
            filters.append(f"from_publication_date:{date_from.isoformat()}")
        if date_to:
            filters.append(f"to_publication_date:{date_to.isoformat()}")
        if filters:
            params["filter"] = ",".join(filters)
        if sort:
            params["sort"] = sort
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=20)
        try:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
            return [self._parse(x) for x in r.json().get("results", [])]
        finally:
            if owns:
                await client.aclose()

    async def resolve_author(self, name: str) -> Author | None:
        """Resolve a human-readable author name to an OpenAlex author ID.

        OpenAlex recommends resolving ambiguous names to entity IDs before filtering
        works. Exact normalized display-name matches are preferred when available.
        """
        params: dict[str, str | int] = {"search": name, "per_page": 10, **self._auth_params()}
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=20)
        try:
            r = await client.get(self.authors_url, params=params)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            target = " ".join(name.casefold().split())
            exact = [x for x in results if " ".join(str(x.get("display_name", "")).casefold().split()) == target]
            x = exact[0] if exact else results[0]
            return Author(name=x.get("display_name") or name, id=_openalex_tail(x.get("id")))
        finally:
            if owns:
                await client.aclose()

    async def author_works(self, author_id: str, query: str, limit: int = 1000) -> tuple[list[Paper], int]:
        """Return topic-relevant works for one OpenAlex author.

        Uses exact author-ID filtering and cursor pagination. `total_available` is
        returned separately so callers can state clearly if a user-requested limit
        truncated the available result set.
        """
        aid = _openalex_tail(author_id)
        if not aid:
            return [], 0
        page_size = min(100, max(1, limit))
        cursor: str | None = "*"
        out: list[Paper] = []
        total_available = 0
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=25)
        try:
            while cursor and len(out) < limit:
                params: dict[str, str | int] = {
                    "search": query,
                    "filter": f"authorships.author.id:{aid}",
                    "per_page": min(page_size, limit - len(out)),
                    "cursor": cursor,
                    **self._auth_params(),
                }
                r = await client.get(self.base_url, params=params)
                r.raise_for_status()
                payload = r.json()
                total_available = int((payload.get("meta") or {}).get("count") or total_available or 0)
                results = payload.get("results", [])
                out.extend(self._parse(x) for x in results)
                cursor = (payload.get("meta") or {}).get("next_cursor")
                if not results:
                    break
            return out[:limit], total_available
        finally:
            if owns:
                await client.aclose()

    def _parse(self, x: dict) -> Paper:
        pub_date = None
        if x.get("publication_date"):
            try:
                pub_date = date.fromisoformat(x["publication_date"])
            except ValueError:
                pass
        authors = []
        institutions: list[str] = []
        for a in x.get("authorships", []):
            insts = [i.get("display_name") for i in a.get("institutions", []) if i.get("display_name")]
            institutions.extend(insts)
            au = a.get("author") or {}
            if au.get("display_name"):
                authors.append(Author(name=au["display_name"], id=_openalex_tail(au.get("id")), institutions=insts))
        primary = x.get("primary_location") or {}
        source = primary.get("source") or {}
        venue = canonical_venue(source.get("display_name"))
        ids = x.get("ids") or {}
        evidence = [
            Evidence(field="cited_by_count", value=x.get("cited_by_count", 0), source="OpenAlex", confidence=1.0),
        ]
        if venue:
            evidence.append(Evidence(field="venue", value=venue, source="OpenAlex", confidence=0.9))
        for inst in sorted(set(institutions)):
            evidence.append(Evidence(field="institution", value=inst, source="OpenAlex authorship", confidence=0.9))
        return Paper(
            id=_openalex_tail(x.get("id")) or ids.get("openalex", "unknown"),
            title=x.get("display_name") or x.get("title") or "Untitled",
            abstract=_invert_abstract(x.get("abstract_inverted_index")),
            publication_date=pub_date,
            venue=venue,
            venue_id=source.get("id"),
            publication_status=x.get("type"),
            authors=authors,
            institutions=sorted(set(institutions)),
            cited_by_count=x.get("cited_by_count") or 0,
            referenced_works=[_openalex_tail(r) or r for r in x.get("referenced_works", [])],
            doi=ids.get("doi") or x.get("doi"),
            external_ids={k: str(v) for k, v in ids.items() if v},
            primary_url=primary.get("landing_page_url") or ids.get("doi"),
            pdf_url=primary.get("pdf_url"),
            evidence=evidence,
            source_records=["OpenAlex"],
        )
