from __future__ import annotations
import httpx


class DBLPProvider:
    base_url = "https://dblp.org/search/publ/api"
    def __init__(self, client: httpx.AsyncClient | None = None): self.client = client
    async def search_title(self, title: str, limit: int = 5) -> list[dict]:
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15)
        try:
            r = await client.get(self.base_url, params={"q": title, "h": limit, "format": "json"})
            r.raise_for_status()
            hits = r.json().get("result", {}).get("hits", {}).get("hit", [])
            return hits if isinstance(hits, list) else [hits]
        finally:
            if owns: await client.aclose()
