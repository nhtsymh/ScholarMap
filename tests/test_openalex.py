from scholarmap.providers.openalex import OpenAlexProvider


def test_openalex_parse():
    x={
      "id":"https://openalex.org/W1","display_name":"Paper A","publication_date":"2025-04-01","cited_by_count":42,
      "abstract_inverted_index":{"hello":[0],"world":[1]},"referenced_works":["https://openalex.org/W0"],
      "ids":{"doi":"https://doi.org/10.1/a"},
      "authorships":[{"author":{"id":"A1","display_name":"Alice"},"institutions":[{"display_name":"Stanford University"}]}],
      "primary_location":{"landing_page_url":"https://example.com/a","pdf_url":"https://example.com/a.pdf","source":{"id":"S1","display_name":"International Conference on Learning Representations"}},
      "type":"article"
    }
    p=OpenAlexProvider()._parse(x)
    assert p.id=="W1"
    assert p.abstract=="hello world"
    assert p.venue=="ICLR"
    assert "Stanford University" in p.institutions
    assert p.referenced_works==["W0"]
