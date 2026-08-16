from __future__ import annotations
import httpx


class OpenReviewProvider:
    """Minimal OpenReview v2 helper for venue-backed verification.

    ScholarMap's MVP does not crawl every venue. This adapter exposes a stable
    boundary that can be expanded with per-venue invitation IDs without changing
    the rest of the application.
    """
    base_url = "https://api2.openreview.net"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def get_notes(self, invitation: str, limit: int = 1000) -> list[dict]:
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=20)
        try:
            r = await client.get(f"{self.base_url}/notes", params={"invitation": invitation, "limit": limit})
            r.raise_for_status()
            return r.json().get("notes", [])
        finally:
            if owns: await client.aclose()
