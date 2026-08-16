from __future__ import annotations
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, HttpUrl


class EvidenceConfidence(str, Enum):
    verified = "verified"
    inferred = "inferred"
    unknown = "unknown"


class Evidence(BaseModel):
    field: str
    value: Any
    source: str
    confidence: float = Field(ge=0, le=1)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    note: str | None = None


class Author(BaseModel):
    name: str
    id: str | None = None
    institutions: list[str] = Field(default_factory=list)


class Repository(BaseModel):
    url: str
    stars: int | None = None
    official: bool = False
    confidence: float = Field(default=0.0, ge=0, le=1)


class Paper(BaseModel):
    id: str
    title: str
    abstract: str = ""
    publication_date: date | None = None
    venue: str | None = None
    venue_id: str | None = None
    publication_status: str | None = None
    authors: list[Author] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    cited_by_count: int = 0
    referenced_works: list[str] = Field(default_factory=list)
    doi: str | None = None
    arxiv_id: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)
    repositories: list[Repository] = Field(default_factory=list)
    primary_url: str | None = None
    pdf_url: str | None = None
    is_survey: bool = False
    evidence: list[Evidence] = Field(default_factory=list)
    source_records: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @property
    def year(self) -> int | None:
        return self.publication_date.year if self.publication_date else None


class SearchRequest(BaseModel):
    topic: str = Field(min_length=2)
    date_from: str = Field(pattern=r"^\d{4}-\d{2}$")
    date_to: str = Field(pattern=r"^\d{4}-\d{2}$")
    sections: list[str] = Field(default_factory=lambda: [
        "top_conference", "strong_labs", "most_cited", "surveys", "classics", "open_source"
    ])
    venues: list[str] | None = None
    labs: list[str] | None = None
    sort: str = "recommended"
    papers_per_section: int = Field(default=10, ge=1, le=50)
    live: bool = False


class PaperCard(BaseModel):
    id: str
    title: str
    authors: list[str]
    author_details: list[Author] = Field(default_factory=list)
    institutions: list[str]
    venue: str | None
    publication_date: date | None
    citations: int
    impact_percentile: float | None = None
    abstract: str
    repositories: list[Repository]
    why_it_matters: str
    tags: list[str]
    links: dict[str, str]
    scores: dict[str, float]
    evidence: list[Evidence] = Field(default_factory=list)


class SearchSection(BaseModel):
    key: str
    title: str
    papers: list[PaperCard]
    groups: dict[str, list[PaperCard]] | None = None


class SearchResponse(BaseModel):
    topic: str
    date_from: str
    date_to: str
    candidate_count: int
    sections: list[SearchSection]
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthorPapersRequest(BaseModel):
    author_id: str | None = None
    author_name: str = Field(min_length=1)
    topic: str = Field(min_length=2)
    live: bool = False
    limit: int = Field(default=200, ge=1, le=1000)


class AuthorPapersResponse(BaseModel):
    author: Author
    topic: str
    paper_count: int
    papers: list[PaperCard]
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
