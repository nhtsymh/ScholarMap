from __future__ import annotations
from datetime import date
from .models import Paper, Author, Repository, Evidence


AUTHORS = {
    "maya": Author(name="Maya Chen", id="A-DEMO-MAYA", institutions=["Stanford University"]),
    "daniel": Author(name="Daniel Park", id="A-DEMO-DANIEL", institutions=["Carnegie Mellon University"]),
    "sofia": Author(name="Sofia Ramirez", id="A-DEMO-SOFIA", institutions=["Google DeepMind"]),
    "amina": Author(name="Amina Yusuf", id="A-DEMO-AMINA", institutions=["Carnegie Mellon University"]),
    "ken": Author(name="Ken Ito", id="A-DEMO-KEN", institutions=["MIT"]),
    "elias": Author(name="Elias Novak", id="A-DEMO-ELIAS", institutions=["Example University"]),
}


def demo_papers() -> list[Paper]:
    # Synthetic-but-realistic fixture papers. Titles and authors are fictional so demo mode
    # cannot be mistaken for live scholarly facts.
    data = [
        ("P1", "Continual Adaptation of Large Language Models", date(2025,2,10), "ICLR", 180, ["Stanford University"], ["P0"], True, 3200, ["maya", "daniel"]),
        ("P2", "Lifelong Memory for Language Model Agents", date(2025,5,12), "ICML", 125, ["Google DeepMind"], ["P0","P1"], True, 5100, ["sofia", "maya"]),
        ("P3", "A Survey of Continual Learning for Foundation Models", date(2025,7,1), None, 90, ["Carnegie Mellon University"], ["P0","P1","P2"], False, 0, ["daniel", "amina"]),
        ("P4", "Online Adaptation without Catastrophic Forgetting", date(2026,1,18), "ICLR", 75, ["MIT"], ["P1"], True, 1800, ["maya", "ken"]),
        ("P5", "Continual Pretraining for Evolving Language Models", date(2026,3,20), "NeurIPS", 68, ["Google DeepMind"], ["P1","P2"], True, 2400, ["sofia", "ken"]),
        ("P6", "Model Editing for Factual Updates", date(2026,4,2), "ICML", 60, ["Example University"], ["P0"], False, 0, ["elias"]),
        ("P7", "Persistent Skills in LLM Agents", date(2026,5,5), None, 42, ["Stanford University"], ["P2","P4"], True, 900, ["daniel", "sofia"]),
        ("P8", "Continual Fine-Tuning with Modular Adapters", date(2026,6,15), "ICML", 35, ["Carnegie Mellon University"], ["P1","P4"], True, 700, ["amina", "maya"]),
        ("P0", "Learning without Forgetting in Neural Systems", date(2018,6,1), "NeurIPS", 3000, ["University of Example"], [], False, 0, ["maya"]),
        ("P9", "A Broad Review of Lifelong Machine Learning", date(2023,1,1), None, 800, ["University of Example"], ["P0"], False, 0, ["amina"]),
        ("P10", "Continual Language Model Adaptation at Scale", date(2024,2,1), "NeurIPS", 240, ["Google DeepMind"], ["P0"], True, 1100, ["sofia"]),
        ("P11", "Persistent Learning in Foundation Models", date(2024,5,1), "ICML", 190, ["Stanford University"], ["P0"], True, 950, ["daniel"]),
        ("P12", "Modular Continual Learning for Neural Models", date(2024,7,1), "ICLR", 150, ["Carnegie Mellon University"], ["P0"], False, 0, ["amina"]),
    ]
    out=[]
    for pid,title,d,venue,cites,insts,refs,open_,stars,author_keys in data:
        repos=[]
        if open_:
            repos=[Repository(url=f"https://github.com/scholarmap-demo/{pid.lower()}", stars=stars, official=True, confidence=1)]
        authors=[]
        for key in author_keys:
            base=AUTHORS[key]
            authors.append(Author(name=base.name,id=base.id,institutions=insts or base.institutions))
        out.append(Paper(
            id=pid,title=title,abstract=title + ". This synthetic fixture is used to exercise ScholarMap ranking, author exploration, and UI without live APIs.",
            publication_date=d,venue=venue,authors=authors,institutions=insts,
            cited_by_count=cites,referenced_works=refs,repositories=repos,is_survey=("survey" in title.lower() or "review" in title.lower()),
            primary_url=f"https://example.org/{pid}",source_records=["demo"],
            evidence=[Evidence(field="fixture",value=True,source="ScholarMap demo",confidence=1.0)]
        ))
    return out
