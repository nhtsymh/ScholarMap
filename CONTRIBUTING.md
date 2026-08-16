# Contributing to ScholarMap

Thank you for improving ScholarMap.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Run the test suite before opening a pull request:

```bash
pytest
```

## Project boundaries

ScholarMap is primarily a scholarly retrieval, ranking, graph, and evidence system. Contributions should preserve the separation between provider-derived facts and generated explanations.

Useful contribution areas include:

- scholarly provider adapters
- author / paper / institution entity resolution
- scientific information retrieval
- citation-graph ranking
- ranking evaluation
- repository verification
- API and web UI improvements
- tests and documentation

## Pull requests

1. Create a focused branch.
2. Add or update tests for behavior changes.
3. Keep provider I/O isolated behind provider classes.
4. Do not silently change ranking semantics; document algorithm changes in `ALGORITHMS.md`.
5. Run `pytest` locally.
6. Open a pull request with a concise problem statement and implementation summary.
