from datetime import date
from scholarmap.models import Paper
from scholarmap.ranking.foundation import foundation_rank


def test_foundation_prefers_branching_ancestor():
    # A is cited by three branches. X is a narrow chain with high raw citation count.
    papers=[
      Paper(id="A",title="continual learning foundation",abstract="continual learning",publication_date=date(2018,1,1),cited_by_count=500,referenced_works=[]),
      Paper(id="B",title="continual pretraining",abstract="continual learning",publication_date=date(2020,1,1),cited_by_count=120,referenced_works=["A"]),
      Paper(id="C",title="lifelong agents",abstract="continual learning agents",publication_date=date(2021,1,1),cited_by_count=110,referenced_works=["A"]),
      Paper(id="D",title="online adaptation",abstract="continual learning adaptation",publication_date=date(2022,1,1),cited_by_count=100,referenced_works=["A"]),
      Paper(id="X",title="continual learning narrow method",abstract="continual learning",publication_date=date(2019,1,1),cited_by_count=900,referenced_works=[]),
      Paper(id="Y",title="narrow followup",abstract="continual learning",publication_date=date(2021,1,1),cited_by_count=300,referenced_works=["X"]),
    ]
    s=foundation_rank("continual learning",papers,date(2026,1,1))
    assert s["A"] > s["X"]

def test_foundation_scores_bounded():
    papers=[Paper(id="A",title="x",publication_date=date(2020,1,1)),Paper(id="B",title="y",publication_date=date(2021,1,1),referenced_works=["A"])]
    s=foundation_rank("x",papers,date(2026,1,1))
    assert all(0 <= v <= 1 for v in s.values())
