import pytest

from qanuntrace import LegalRecord
from qanuntrace.adapters import MemoryStore
from qanuntrace.graph import Edge, EvidenceGraph


def test_graph_provenance_and_bounded_traversal():
    a = LegalRecord.make('a','law','v1','article','1','المادة 2 مرتبطة','fixture:a')
    b = LegalRecord.make('b','law','v1','article','2','نص آخر','fixture:b')
    graph = EvidenceGraph(MemoryStore([a,b]))
    edge = Edge('a','b','cites','a',0,6,'المادة',reviewed_by='legal-editor')
    graph.add(edge)
    assert [x.source_id for x in graph.expand('a')] == ['a','b']
    assert [x.source_id for x in graph.expand('a',max_hops=0)] == ['a']
    with pytest.raises(ValueError):
        graph.add(Edge('a','b','applies','a',0,6,'المادة'))
    with pytest.raises(ValueError):
        graph.add(Edge('a','b','mentions','a',0,6,'متناقض'))
