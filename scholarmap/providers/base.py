from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from ..models import Paper


class PaperProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, date_from: date | None = None, date_to: date | None = None,
                     limit: int = 100, sort: str | None = None) -> list[Paper]:
        raise NotImplementedError
