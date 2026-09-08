# ScholarMap

### Query-Conditioned Scholarly Discovery and Research Landscape Ranking System

> **Map a research field. Find what actually matters.**

ScholarMap is an open-source scholarly discovery and ranking system that turns a research question into a structured research landscape. It is designed for researchers who need to decide **what deserves attention**, not just retrieve another long list of textually related papers.

Traditional academic search is very good at answering *“Which papers match my query?”* The harder research workflow begins after retrieval: identifying the conference work that matters, finding the groups that actually lead a specific subfield, comparing recent papers fairly against older ones, locating the best surveys, tracing foundational work, and checking which papers have usable implementations.

ScholarMap models those decisions explicitly with query-conditioned retrieval, scholarly graph ranking, temporal signals, multi-source entity resolution, and evidence-backed metadata.

---

## Core Capabilities

ScholarMap organizes literature into six complementary research views:

- **Top Conference Papers** — topic-relevant work from a transparent, configurable venue registry.
- **Strong Labs / Companies** — recent work from institutions whose historical contributions are strong for the specific query.
- **Most Cited** — highly cited papers inside the requested period.
- **Surveys** — surveys, reviews, taxonomies, and overview papers for entering a field.
- **Classics / Foundations** — earlier work that structurally shaped the research direction.
- **Open Source** — papers with repository and implementation evidence.

Each paper card can expose:

- title, authors, and affiliations
- venue and publication status
- publication date
- citation count
- topic-age impact percentile
- abstract
- repository metadata and GitHub stars
- research tags
- a grounded “Why it matters” explanation
- paper, arXiv, code, DOI, and BibTeX links

---

## Author Explorer

Every author name in ScholarMap is interactive.

Clicking an author opens **Author Explorer**, which retrieves that author’s **all-time papers relevant to the current research topic** and ranks them using the same ScholarMap relevance and impact pipeline.

For live OpenAlex records, ScholarMap uses a stable author identifier instead of filtering only by a human-readable name. This prevents papers from different researchers with the same name from being silently mixed together.

```text
Current topic
"continual learning for large language models"
            │
            ▼
Click an author
            │
            ▼
Resolve stable author identity
            │
            ▼
Retrieve all topic-matching works by that author
            │
            ▼
AgendaRank + impact ranking
            │
            ▼
Author Explorer
```

Author exploration is intentionally **all-time**: the original search window defines the research landscape, while the author view helps the user understand the researcher’s broader trajectory in that same topic.

---

# Why ScholarMap?

## Relevance is not the same as research importance

Text retrieval can surface papers that contain similar terminology but participate in different research agendas. A query around continual adaptation of large language models, for example, may overlap lexically with model editing, agent memory, continual pretraining, online learning, and parameter-efficient adaptation without those works playing the same role in the research landscape.

ScholarMap therefore combines textual relevance with local scholarly graph structure instead of treating semantic similarity as the final ranking criterion.

## Raw citation counts are temporally biased

Older papers have had more time to accumulate citations. A recent paper with unusually strong early influence can therefore be buried below older papers even when it is already exceptional relative to other work of the same age.

ScholarMap complements raw citations with age-aware impact signals.

## Institutional strength is topic-specific

A globally prominent institution is not equally influential in every research area. ScholarMap therefore estimates institutional strength from **historical topic-relevant work**, rather than using a hard-coded prestige list.

## Foundational work is more than highly cited work

A paper may be foundational because it helped create multiple later research branches, even if another paper accumulated more citations. ScholarMap models that structural role inside a query-conditioned citation graph.

---

# Ranking Engine

ScholarMap is built around three query-conditioned ranking modules.

## AgendaRank

**AgendaRank** estimates whether a candidate paper belongs to the same research agenda as the user’s query.

```text
Research Query
      │
      ▼
High-Recall Retrieval
      │
      ▼
Candidate Papers
      │
      ▼
Local Citation Graph
      │
      ▼
Research Communities
      │
      ▼
Query ↔ Community Alignment
      │
      ▼
AgendaRank
```

A simplified formulation is:

$$
A(p \mid q)
=
\alpha S_{\mathrm{text}}(p,q)
+
\beta S_{\mathrm{agenda}}(p,q)
+
\gamma S_{\mathrm{graph}}(p,q)
$$

where the three terms represent textual relevance, research-community alignment, and local graph structure.

The goal is to distinguish papers that merely **share vocabulary** from papers that participate in the same research trajectory.

---

## LabRank

**LabRank** estimates institutional research strength for the specific topic being searched.

For an institution $L$, query $q$, and search-window start time $t$:

$$
\operatorname{LabRank}(L \mid q,t)
=
\sum_{p \in P_L,\;\operatorname{time}(p)<t}
R(p \mid q)\,I(p)\,V(p)\,D(p,t)
$$

The central constraint is temporal:

> **Only work published before the requested search window may influence institutional strength.**

```text
Historical topic-relevant work
          │
          ▼
Institution research impact
          │
          ▼
Topic-conditioned LabRank
          │
          ▼
Recent work during the target period
```

This prevents future-information leakage: a new paper cannot retroactively make its own institution appear stronger and then receive a ranking boost for coming from that institution.

---

## FoundationRank

**FoundationRank** identifies papers that structurally shaped the development of a research topic.

It combines:

- query-conditioned citation centrality
- downstream research-community breadth
- normalized research impact

A simplified formulation is:

$$
F(p \mid q)=C_q(p)\,B(p)\,I(p)
$$

Conceptually:

```text
                 Foundational Paper
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     Research A     Research B     Research C
          │             │             │
          ▼             ▼             ▼
      Later Work     Later Work     Later Work
```

This makes “foundational” a topic-conditioned structural property rather than a synonym for “old and highly cited.”

---

# Query-Conditioned Scholarly Graph

The ranking modules operate on a local scholarly graph constructed for each query.

```text
                 Research Topic
                       +
                  Time Window
                       │
                       ▼
                Query Processing
                       │
                       ▼
              High-Recall Retrieval
                       │
                       ▼
            Canonical Paper Resolution
                       │
                       ▼
         Query-Conditioned Scholarly Graph
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       AgendaRank   LabRank  FoundationRank
            │          │          │
            └──────────┼──────────┘
                       ▼
                 Impact Signals
                       │
                       ▼
                 Evidence Ledger
                       │
                       ▼
                Research Landscape
```

The graph can connect:

```text
Paper
Author
Institution
Venue
Repository
Citation
```

---

# Topic-Age Impact

Citation totals are difficult to compare across publication ages. ScholarMap therefore supports age-aware impact signals that place a paper in the context of similarly aged work.

```text
Citations
76

Topic-Age Impact Percentile
99.2%
```

The percentile complements raw citation counts rather than replacing them.

---

# Canonical Paper Resolution

The same work may appear simultaneously as an arXiv preprint, OpenReview submission, conference publication, DOI record, OpenAlex work, or DBLP record.

ScholarMap resolves these records into one canonical paper entity using evidence ordered approximately from strongest to weaker signals:

```text
DOI exact match
       │
       ▼
arXiv identifier
       │
       ▼
Known scholarly identifiers
       │
       ▼
Normalized title + author overlap
       │
       ▼
Title / abstract similarity
```

False-merge protection is included so distinct papers with similar titles are not automatically collapsed into one record.

---

# Evidence Ledger

ScholarMap treats scholarly facts as evidence-backed data.

Instead of storing only:

```json
{
  "venue": "ICLR 2026"
}
```

ScholarMap can retain provenance:

```json
{
  "field": "venue",
  "value": "ICLR 2026",
  "source": "OpenAlex",
  "confidence": 0.90
}
```

Evidence can be attached to fields such as venue, publication status, date, affiliation, citation count, and repository information.

> **Algorithms rank. Data sources ground. Explanations stay evidence-aware.**

Language models are not treated as authoritative sources of scholarly facts.

---

# Scholarly Data Providers

ScholarMap uses a provider-based architecture.

| Provider | Role |
|---|---|
| **OpenAlex** | scholarly graph, papers, authors, institutions, citations |
| **arXiv** | recent preprints and abstracts |
| **OpenReview** | conference submissions and publication metadata |
| **Crossref** | DOI and formal publication metadata |
| **DBLP** | computer-science publication metadata |
| **GitHub** | repository metadata and stars |

The main live discovery path uses OpenAlex and arXiv. Other providers are isolated behind adapters so metadata enrichment can evolve without rewriting the ranking engine.

---

# Web Interface

ScholarMap includes a browser-based interface for interactive literature discovery.

Users can configure:

- research topic
- start and end month
- requested landscape sections
- ranking preference
- number of papers per section
- demo or live scholarly retrieval

Author names inside paper cards are clickable and open Author Explorer without leaving the current research landscape.

---

# Quick Start

## 1. Create a virtual environment

```bash
python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

## 2. Install ScholarMap

```bash
pip install -e .
```

## 3. Start the web application

```bash
uvicorn scholarmap.app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

ScholarMap starts in a clearly labeled synthetic demo mode so the complete interface and ranking pipeline can be exercised without depending on third-party API availability. Enable **Live public APIs** in the web interface to use live scholarly retrieval.

---

# Command Line Interface

```bash
scholarmap \
  "continual learning for large language models" \
  --from 2025-01 \
  --to 2026-07
```

Live retrieval:

```bash
scholarmap \
  "test-time scaling for large language models" \
  --from 2025-01 \
  --to 2026-07 \
  --live
```

---

# Configuration

Optional environment variables:

```bash
OPENALEX_API_KEY=...
GITHUB_TOKEN=...
```

These can be used for more reliable live scholarly retrieval and repository enrichment.

---

# API

ScholarMap exposes a FastAPI HTTP interface.

## Build a research landscape

```http
POST /api/search
```

Example request:

```json
{
  "topic": "continual learning for large language models",
  "date_from": "2025-01",
  "date_to": "2026-07",
  "sections": [
    "top_conference",
    "strong_labs",
    "most_cited",
    "surveys",
    "classics",
    "open_source"
  ]
}
```

## Explore an author inside the current research topic

```http
POST /api/authors/papers
```

Example:

```json
{
  "author_id": "A5023888391",
  "author_name": "Example Researcher",
  "topic": "continual learning for large language models",
  "live": true,
  "limit": 1000
}
```

The author view is all-time and topic-conditioned.

## Additional endpoints

```text
GET  /health
GET  /api/paper/{paper_id}
GET  /api/evidence/{paper_id}
POST /api/export/bibtex
```

FastAPI also exposes interactive OpenAPI documentation at:

```text
http://127.0.0.1:8000/docs
```

---

# Project Structure

```text
ScholarMap/
│
├── scholarmap/
│   ├── providers/
│   │   ├── openalex.py
│   │   ├── arxiv.py
│   │   ├── openreview.py
│   │   ├── crossref.py
│   │   ├── dblp.py
│   │   └── github.py
│   │
│   ├── ranking/
│   │   ├── agenda.py
│   │   ├── lab.py
│   │   ├── foundation.py
│   │   ├── impact.py
│   │   └── recommended.py
│   │
│   ├── static/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   │
│   ├── app.py
│   ├── cli.py
│   ├── models.py
│   ├── resolver.py
│   └── service.py
│
├── tests/
├── .github/workflows/ci.yml
├── ALGORITHMS.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

---

# Testing

Run the complete test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=scholarmap --cov-report=term-missing
```

The suite covers:

- DOI, arXiv, and title-based canonicalization
- false-merge protection
- AgendaRank citation-community behavior
- LabRank topic specificity and strict temporal cutoff
- future-information leakage prevention
- FoundationRank graph breadth and centrality
- topic-age impact normalization
- OpenAlex and arXiv parsing
- provider HTTP contracts
- OpenAlex author-ID resolution and author-work filtering
- Author Explorer demo and live-ID paths
- search section construction and ordering
- health, search, paper, evidence, author, and BibTeX endpoints
- CLI behavior
- frontend Author Explorer hooks

Current automated test status:

```text
43 tests passed
94% Python test coverage
```

---

# Design Principles

### Retrieval first, generation second

ScholarMap treats scholarly discovery primarily as an information-retrieval and ranking problem. Generated prose never replaces structured scholarly evidence.

### Query-conditioned importance

There is no universal definition of an important paper or a strong institution. Ranking is conditioned on the research question and its local scholarly structure.

### Stable author identity

Author exploration uses provider identifiers whenever possible rather than assuming a human-readable name uniquely identifies a researcher.

### Temporal correctness

Historical and target-window evidence are explicitly separated where necessary to avoid information leakage.

### Evidence-backed metadata

Facts remain connected to their sources and confidence signals whenever available.

### Modular scholarly infrastructure

Providers, entity resolution, ranking, evidence, application services, and presentation are separated so each layer can evolve independently.

---

# Algorithm Documentation

Detailed implementation notes for AgendaRank, LabRank, FoundationRank, entity resolution, and impact normalization are available in [`ALGORITHMS.md`](ALGORITHMS.md).

---

# Contributing

Contributions are welcome across scientific information retrieval, scholarly graph construction, ranking, entity resolution, provider integrations, repository verification, evaluation, frontend development, and documentation.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow.

---

# License

ScholarMap is released under the **MIT License**. See [`LICENSE`](LICENSE).

---

<p align="center">
  <strong>ScholarMap</strong><br>
  <em>Map a research field. Find what actually matters.</em>
</p>
