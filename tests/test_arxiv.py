from scholarmap.providers.arxiv import ArxivProvider

ATOM='''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
 <entry><id>http://arxiv.org/abs/2501.12345v2</id><updated>2025-01-03T00:00:00Z</updated><published>2025-01-02T00:00:00Z</published>
 <title>  A Great Paper  </title><summary> Test abstract </summary><author><name>Alice</name></author>
 <link title="pdf" href="https://arxiv.org/pdf/2501.12345"/><arxiv:doi>10.1000/test</arxiv:doi></entry></feed>'''

def test_parse_atom():
    ps=ArxivProvider.parse_atom(ATOM)
    assert len(ps)==1
    p=ps[0]
    assert p.arxiv_id=="2501.12345"
    assert p.title=="A Great Paper"
    assert p.authors[0].name=="Alice"
    assert p.doi=="10.1000/test"
