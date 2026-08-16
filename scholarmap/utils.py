from __future__ import annotations
import math
import re
from datetime import date
from calendar import monthrange


def normalize_title(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def month_start(s: str) -> date:
    y, m = map(int, s.split("-"))
    return date(y, m, 1)


def month_end(s: str) -> date:
    y, m = map(int, s.split("-"))
    return date(y, m, monthrange(y, m)[1])


def months_between(start: date | None, end: date) -> int:
    if not start:
        return 1
    return max(1, (end.year - start.year) * 12 + end.month - start.month + 1)


def minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return [1.0 if hi > 0 else 0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def canonical_venue(name: str | None) -> str | None:
    if not name:
        return None
    from .config import VENUE_ALIASES
    low = name.lower().strip()
    for key, val in VENUE_ALIASES.items():
        if key in low:
            return val
    return name.strip()
