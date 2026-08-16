from __future__ import annotations
import os
import httpx
from ..models import Repository
from ..utils import normalize_title


class GitHubProvider:
    base_url = "https://api.github.com"

    def __init__(self, client: httpx.AsyncClient | None = None, token: str | None = None):
        self.client = client
        self.token = token or os.getenv("GITHUB_TOKEN")

    async def find_repository(self, title: str, arxiv_id: str | None = None) -> Repository | None:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        owns = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15, headers=headers)
        try:
            q = f'"{title}" in:name,description,readme'
            r = await client.get(f"{self.base_url}/search/repositories", params={"q": q, "per_page": 5})
            if r.status_code == 403:
                return None
            r.raise_for_status()
            best = None
            best_score = 0.0
            nt = set(normalize_title(title).split())
            for item in r.json().get("items", []):
                blob = normalize_title(" ".join([item.get("name", ""), item.get("description") or ""]))
                overlap = len(nt & set(blob.split())) / max(1, len(nt))
                score = overlap
                if arxiv_id and arxiv_id.lower() in (item.get("description") or "").lower():
                    score += 0.5
                if score > best_score:
                    best_score, best = score, item
            if not best or best_score < 0.25:
                return None
            return Repository(url=best["html_url"], stars=best.get("stargazers_count", 0),
                              official=False, confidence=min(0.8, best_score))
        finally:
            if owns: await client.aclose()
