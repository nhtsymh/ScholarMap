from datetime import date
from scholarmap.models import Paper, Author
from scholarmap.resolver import same_paper, canonicalize


def paper(id,title,doi=None,arxiv=None,authors=("A",)):
    return Paper(id=id,title=title,doi=doi,arxiv_id=arxiv,authors=[Author(name=x) for x in authors],publication_date=date(2025,1,1))

def test_same_doi():
    assert same_paper(paper("a","X","10.1/ABC"), paper("b","Y","https://doi.org/10.1/abc"))

def test_same_arxiv():
    assert same_paper(paper("a","A","", "2501.12345"), paper("b","B",None,"2501.12345"))

def test_title_variant_author_overlap():
    a=paper("a","Continual Learning for Large Language Models",authors=("Jane Doe","John X"))
    b=paper("b","Continual Learning for Large Language Models: A Comprehensive Study",authors=("Jane Doe","Mary Y"))
    assert same_paper(a,b)

def test_similar_title_but_different_authors_not_forced_merge():
    a=paper("a","A Study of Neural Networks for Vision",authors=("Alice",))
    b=paper("b","A Study of Neural Networks for Language",authors=("Bob",))
    assert not same_paper(a,b)

def test_canonicalize_merges_sources():
    a=paper("a","Continual Learning for Large Language Models",doi="10.1/a")
    a.source_records=["OpenAlex"]
    b=paper("b","Continual Learning for Large Language Models",doi="10.1/a")
    b.source_records=["arXiv"]
    out=canonicalize([a,b])
    assert len(out)==1
    assert set(out[0].source_records)=={"OpenAlex","arXiv"}
