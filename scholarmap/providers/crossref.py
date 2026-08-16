from __future__ import annotations
import httpx


class CrossrefProvider:
    base_url = "https://api.crossref.org/works"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def lookup_title(self, title: str) -> dict | None:
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15, headers={"User-Agent": "ScholarMap/0.1"})
        try:
            r = await client.get(self.base_url, params={"query.title": title, "rows": 1})
            r.raise_for_status()
            items = r.json().get("message", {}).get("items", [])
            return items[0] if items else None
        finally:
            if owns: await client.aclose()
