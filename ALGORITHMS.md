# ScholarMap Algorithms

This file documents the algorithmic core separately from provider plumbing and UI.

## 1. AgendaRank

**Goal:** reduce papers that are textually similar to the query but belong to a different research agenda.

For the current query result set, ScholarMap builds a local directed citation graph (`citing -> cited`) and computes:

- `S_text`: TF-IDF title+abstract relevance to the query (replaceable by a dense scientific embedding model).
- `S_agenda`: mean query relevance of the paper's citation community, discovered with greedy modularity on the local undirected projection.
- `S_graph`: normalized PageRank-like graph centrality.

Current score:

```text
AgendaRank(p|q) = 0.65*S_text + 0.25*S_agenda + 0.10*S_graph
```

The components are intentionally modular: scientific embeddings or alternative community detection can be swapped in without changing section construction.

## 2. LabRank

**Goal:** identify institutions that are strong for *this particular topic*, rather than using a hard-coded global-prestige list.

Only papers published **before the user's search window** are eligible, preventing information leakage from the target period.

```text
LabRank(L|q,t) = sum over historical papers p from L of:
    relevance(p,q)
  * (1 + age_normalized_impact(p,t))
  * venue_signal(p)
  * exp(-0.18 * years_old)
  / number_of_institutions_on_paper
```

Scores are normalized by the highest-scoring institution for the query.

## 3. FoundationRank

**Goal:** find papers that structurally shaped the query-specific field, rather than merely accumulating many citations.

The score combines:

- query-conditioned citation centrality (personalized PageRank over the local citation graph),
- downstream breadth (direct independent citing branches plus citation-community breadth within three hops),
- age-normalized citation impact.

```text
FoundationRank(p|q) = 0.45*Centrality + 0.35*Breadth + 0.20*Impact
```

A synthetic-graph regression test ensures a work that seeds multiple downstream branches can outrank a high-citation work that only sits on a narrow chain.

## 4. Topic-age impact percentile

Raw citations are biased by exposure time. For each paper, the current implementation compares it with papers in the current query result whose ages differ by at most six months and reports the percentile of its citation count in that cohort.

This is deliberately called an **impact percentile**, not "citation velocity". True 30/90-day momentum requires stored historical snapshots; ScholarMap therefore does not label age-normalized impact as recent citation growth.

## 5. Canonical paper resolution

Strong identifiers are checked first:

1. DOI exact match
2. arXiv ID exact match
3. normalized exact title
4. fuzzy title + token containment + author overlap

Merging preserves provenance from all source records. Conservative thresholds protect against false merges.

## 6. Evidence Ledger

Every provider-backed fact can carry:

```text
field / value / source / confidence / fetched_at / note
```

This separates facts from ranking logic. The design principle is:

> **Algorithms rank. Data sources ground. LLMs explain.**

V0.1 does not require an LLM; `Why it matters` uses grounded templates so the application is fully runnable and testable without an API key.


## 7. Author Explorer and stable author identity

Author exploration is topic-conditioned but all-time. When an OpenAlex author ID is available on a paper record, ScholarMap filters works by that stable ID and the current research query. If a paper source does not provide a stable author ID, ScholarMap first resolves the author name to an OpenAlex author entity and only then retrieves works.

```text
clicked author -> stable author ID -> author-filtered topic retrieval -> AgendaRank -> author paper view
```

This avoids treating a human-readable author name as a unique identifier and reduces same-name author collisions.
