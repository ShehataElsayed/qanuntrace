import pytest

from qanuntrace.ontology import Concept, CuratedOntology


def test_reviewed_aliases_are_search_hints():
    c = Concept('case', 'دعوى', ('قضية',), 'reviewer', '2026-09-27')
    o = CuratedOntology((c,))
    assert o.candidates('عندي قضية') == ('case',)
    with pytest.raises(ValueError):
        CuratedOntology((c, Concept('other','قضية',(), 'reviewer','2026-09-27')))
