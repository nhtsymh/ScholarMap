from scholarmap.fixtures import demo_papers

def test_demo_papers_have_provenance():
    for p in demo_papers():
        assert p.evidence
        assert all(0 <= e.confidence <= 1 for e in p.evidence)
