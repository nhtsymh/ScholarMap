from datetime import date
from scholarmap.models import Paper
from scholarmap.ranking.lab import lab_rank


def p(id,title,d,inst,cites=20,venue="ICLR"):
    return Paper(id=id,title=title,abstract=title,publication_date=d,institutions=[inst],cited_by_count=cites,venue=venue)

def test_topic_conditioned_lab_rank():
    papers=[
      p("a","continual learning catastrophic forgetting",date(2023,1,1),"Lab A",100),
      p("b","lifelong language model adaptation",date(2024,1,1),"Lab A",80),
      p("c","database query optimization",date(2023,1,1),"Lab B",1000),
    ]
    r=lab_rank("continual learning language models",papers,date(2025,1,1))
    assert r["Lab A"] > r.get("Lab B",0)

def test_no_future_leakage():
    cutoff=date(2025,1,1)
    base=[p("a","continual learning",date(2024,1,1),"Lab A",20),p("b","continual learning",date(2024,2,1),"Lab B",10)]
    before=lab_rank("continual learning",base,cutoff)
    with_future=base+[p("future","continual learning breakthrough",date(2026,1,1),"Lab B",100000)]
    after=lab_rank("continual learning",with_future,cutoff)
    assert before==after
