from datetime import date
from scholarmap.models import Paper
from scholarmap.ranking.agenda import agenda_rank


def test_agenda_rank_rewards_relevant_community():
    papers=[
      Paper(id="A",title="Continual learning for language models",abstract="catastrophic forgetting lifelong adaptation",publication_date=date(2025,1,1),referenced_works=[]),
      Paper(id="B",title="Lifelong adaptation of LLM agents",abstract="continual learning memory catastrophic forgetting",publication_date=date(2025,2,1),referenced_works=["A"]),
      Paper(id="C",title="Model editing for language models",abstract="knowledge editing factual updates language models",publication_date=date(2025,2,1),referenced_works=[]),
      Paper(id="D",title="Editing factual knowledge in LLMs",abstract="model editing factual knowledge updates",publication_date=date(2025,3,1),referenced_works=["C"]),
    ]
    scores=agenda_rank("continual learning for LLMs",papers)
    assert scores["A"] > scores["C"]
    assert scores["B"] > scores["D"]

def test_agenda_rank_no_edges_still_works():
    papers=[Paper(id="A",title="continual learning",publication_date=date(2025,1,1)),Paper(id="B",title="database systems",publication_date=date(2025,1,1))]
    s=agenda_rank("continual learning",papers)
    assert s["A"] > s["B"]
