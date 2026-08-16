from __future__ import annotations
from datetime import date, timedelta
import asyncio
from .models import (
    SearchRequest, SearchResponse, SearchSection, PaperCard, Paper, Author,
    AuthorPapersRequest, AuthorPapersResponse,
)
from .providers.openalex import OpenAlexProvider
from .providers.arxiv import ArxivProvider
from .providers.github import GitHubProvider
from .resolver import canonicalize
from .ranking.agenda import agenda_rank
from .ranking.lab import lab_rank
from .ranking.foundation import foundation_rank
from .ranking.recommended import recommended_scores, venue_score
from .ranking.common import impact_percentiles
from .config import AI_ML_VENUES, SURVEY_TERMS
from .utils import month_start, month_end, canonical_venue
from .explain import why_it_matters
from .fixtures import demo_papers

SECTION_TITLES = {
    "top_conference": "Top Conference Papers",
    "strong_labs": "Strong Labs / Companies",
    "most_cited": "Most Cited",
    "surveys": "Surveys",
    "classics": "Classics / Foundations",
    "open_source": "Open Source",
}


class ScholarMapService:
    def __init__(self, openalex=None, arxiv=None, github=None):
        self.openalex = openalex or OpenAlexProvider()
        self.arxiv = arxiv or ArxivProvider()
        self.github = github or GitHubProvider()
        self.paper_cache: dict[str, Paper] = {}

    async def search(self, req: SearchRequest) -> SearchResponse:
        start, end = month_start(req.date_from), month_end(req.date_to)
        if start > end:
            raise ValueError("date_from must not be after date_to")
        warnings=[]
        live_ok = False
        if req.live:
            try:
                # Target-window + historical/all-time pools; bounded to keep public APIs polite.
                target_oa, target_ax, classic_pool, historical = await asyncio.gather(
                    self.openalex.search(req.topic, start, end, limit=100),
                    self.arxiv.search(req.topic, start, end, limit=50),
                    self.openalex.search(req.topic, None, end, limit=100, sort="cited_by_count:desc"),
                    self.openalex.search(req.topic, date(max(1990,start.year-6),1,1), start - timedelta(days=1), limit=100),
                )
                target = canonicalize(target_oa + target_ax)
                classic_pool = canonicalize(classic_pool)
                historical = canonicalize(historical)
                live_ok = True
            except Exception as exc:
                warnings.append(f"Live providers failed; demo fixtures used instead: {type(exc).__name__}: {exc}")
                target, classic_pool, historical = self._demo_split(start,end)
        else:
            warnings.append("Demo mode: synthetic fixture papers are shown. Enable live search to query public scholarly APIs.")
            target, classic_pool, historical = self._demo_split(start,end)

        # Optional code enrichment. GitHub search is deliberately bounded because the
        # unauthenticated Search API is rate-limited. It only runs in live mode when
        # the user requested the open-source section.
        if live_ok and "open_source" in req.sections:
            try:
                for p in target[:8]:
                    if not p.repositories:
                        repo = await self.github.find_repository(p.title, p.arxiv_id)
                        if repo:
                            p.repositories.append(repo)
            except Exception as exc:
                warnings.append(f"GitHub enrichment skipped: {type(exc).__name__}: {exc}")

        # Topic-aware ranking on the target landscape.
        agenda = agenda_rank(req.topic, target)
        rec = recommended_scores(target, agenda, end)
        perc = impact_percentiles(target, end)
        for p in target:
            p.scores.update(agenda=agenda.get(p.id,0), recommended=rec.get(p.id,0), impact_percentile=perc.get(p.id,0))
            p.is_survey = p.is_survey or any(t in p.title.lower() for t in SURVEY_TERMS)

        foundations = foundation_rank(req.topic, classic_pool, end)
        for p in classic_pool:
            p.scores["foundation"] = foundations.get(p.id,0)

        venues = set(req.venues or AI_ML_VENUES)
        cutoff = start
        labs = lab_rank(req.topic, historical, cutoff, venue_signal=lambda v: venue_score(v))
        top_labs = set(req.labs or [x for x,_ in sorted(labs.items(), key=lambda kv: kv[1], reverse=True)[:8]])

        self.paper_cache = {p.id: p for p in canonicalize(target + classic_pool + historical)}

        sections=[]
        for key in req.sections:
            if key not in SECTION_TITLES:
                continue
            groups=None
            if key == "top_conference":
                items=[p for p in target if canonical_venue(p.venue) in venues]
                items=self._sort(items, req.sort)
            elif key == "strong_labs":
                items=[p for p in target if set(p.institutions) & top_labs]
                items=self._sort(items, req.sort)
                groups={}
                for lab in sorted(top_labs):
                    subset=[p for p in items if lab in p.institutions]
                    if subset:
                        groups[lab]=[self._card(p,key) for p in subset[:req.papers_per_section]]
            elif key == "most_cited":
                items=sorted(target,key=lambda p:(p.cited_by_count,p.scores.get("agenda",0)),reverse=True)
            elif key == "surveys":
                # Use target + classic pool so a user can still find the best entry-point survey.
                pool=canonicalize(target+classic_pool)
                items=[p for p in pool if p.is_survey or any(t in p.title.lower() for t in SURVEY_TERMS)]
                items=sorted(items,key=lambda p:(p.scores.get("recommended",0), p.cited_by_count),reverse=True)
            elif key == "classics":
                items=sorted(classic_pool,key=lambda p:p.scores.get("foundation",0),reverse=True)
            elif key == "open_source":
                items=[p for p in target if p.repositories]
                items=sorted(items,key=lambda p:(max([r.stars or 0 for r in p.repositories],default=0),p.scores.get("recommended",0)),reverse=True)
            else:
                items=[]
            cards=[self._card(p,key) for p in items[:req.papers_per_section]]
            sections.append(SearchSection(key=key,title=SECTION_TITLES[key],papers=cards,groups=groups))
        return SearchResponse(topic=req.topic,date_from=req.date_from,date_to=req.date_to,
                              candidate_count=len(target),sections=sections,warnings=warnings)

    async def author_papers(self, req: AuthorPapersRequest) -> AuthorPapersResponse:
        """Explore one author's all-time work that is relevant to a topic.

        In live mode, author identity is resolved to an OpenAlex ID and works are
        fetched with an exact author-ID filter plus the topic search. In demo mode,
        synthetic fixtures are filtered by the same stable author ID/name contract.
        """
        warnings: list[str] = []
        author = Author(name=req.author_name, id=req.author_id)
        papers: list[Paper] = []
        total_available = 0

        if req.live:
            try:
                if not author.id or not str(author.id).split("/")[-1].startswith("A"):
                    resolved = await self.openalex.resolve_author(author.name)
                    if not resolved:
                        raise ValueError(f"Could not resolve author '{author.name}' in OpenAlex")
                    author = resolved
                    warnings.append("Author had no stable OpenAlex ID in the paper record and was resolved by name before retrieval.")
                papers, total_available = await self.openalex.author_works(author.id, req.topic, limit=req.limit)
                papers = canonicalize(papers)
            except Exception as exc:
                warnings.append(f"Live author lookup failed; demo fixtures used instead: {type(exc).__name__}: {exc}")
                author, papers, total_available = self._demo_author_papers(req)
        else:
            warnings.append("Demo mode: author exploration uses synthetic fixture papers.")
            author, papers, total_available = self._demo_author_papers(req)

        if papers:
            agenda = agenda_rank(req.topic, papers)
            as_of = date.today()
            rec = recommended_scores(papers, agenda, as_of)
            perc = impact_percentiles(papers, as_of)
            for p in papers:
                p.scores.update(
                    agenda=agenda.get(p.id,0),
                    recommended=rec.get(p.id,0),
                    impact_percentile=perc.get(p.id,0),
                )
            papers = sorted(
                papers,
                key=lambda p:(p.scores.get("recommended",0), p.publication_date or date.min),
                reverse=True,
            )

        self.paper_cache.update({p.id: p for p in papers})
        cards=[self._card(p,"author") for p in papers]
        if total_available > len(cards):
            warnings.append(f"Showing {len(cards)} of {total_available} topic-matching works because the author-view limit is {req.limit}.")
        return AuthorPapersResponse(
            author=author,
            topic=req.topic,
            paper_count=len(cards),
            papers=cards,
            warnings=warnings,
        )

    def _demo_author_papers(self, req: AuthorPapersRequest) -> tuple[Author, list[Paper], int]:
        allp = demo_papers()
        key_id = (req.author_id or "").casefold()
        key_name = " ".join(req.author_name.casefold().split())
        matches=[]
        resolved: Author | None = None
        for p in allp:
            for a in p.authors:
                same_id = bool(key_id and (a.id or "").casefold() == key_id)
                same_name = " ".join(a.name.casefold().split()) == key_name
                if same_id or same_name:
                    resolved = resolved or a
                    matches.append(p)
                    break
        matches=canonicalize(matches)
        # Demo fixtures are all CL/LLM-adjacent, but AgendaRank still determines order.
        total=len(matches)
        return resolved or Author(name=req.author_name,id=req.author_id), matches[:req.limit], total

    def _demo_split(self,start,end):
        allp=demo_papers()
        target=[p for p in allp if p.publication_date and start <= p.publication_date <= end]
        classic=list(allp)
        historical=[p for p in allp if p.publication_date and p.publication_date < start]
        return target, classic, historical

    @staticmethod
    def _sort(items:list[Paper], mode:str):
        if mode=="citations":
            return sorted(items,key=lambda p:p.cited_by_count,reverse=True)
        if mode=="date":
            return sorted(items,key=lambda p:p.publication_date or date.min,reverse=True)
        if mode=="relevance":
            return sorted(items,key=lambda p:p.scores.get("agenda",0),reverse=True)
        return sorted(items,key=lambda p:p.scores.get("recommended",0),reverse=True)

    @staticmethod
    def _card(p:Paper,section:str):
        links={}
        if p.primary_url:
            links["paper"]=p.primary_url
        if p.pdf_url:
            links["pdf"]=p.pdf_url
        if p.doi:
            links["doi"]=p.doi if p.doi.startswith("http") else f"https://doi.org/{p.doi}"
        if p.arxiv_id:
            links["arxiv"]=f"https://arxiv.org/abs/{p.arxiv_id}"
        if p.repositories:
            links["code"]=p.repositories[0].url
        tags=[]
        if p.venue and canonical_venue(p.venue) in AI_ML_VENUES:
            tags.append("Top Conference")
        if p.repositories:
            tags.append("Open Source")
        if section=="classics":
            tags.append("Classic")
        if section=="strong_labs":
            tags.append("Strong Lab")
        if p.is_survey:
            tags.append("Survey")
        return PaperCard(
            id=p.id,
            title=p.title,
            authors=[a.name for a in p.authors],
            author_details=p.authors,
            institutions=p.institutions,
            venue=p.venue,
            publication_date=p.publication_date,
            citations=p.cited_by_count,
            impact_percentile=p.scores.get("impact_percentile"),
            abstract=p.abstract,
            repositories=p.repositories,
            why_it_matters=why_it_matters(p,section),
            tags=tags,
            links=links,
            scores=p.scores,
            evidence=p.evidence,
        )
