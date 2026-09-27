import pytest

from qanuntrace.adapters import MemoryStore
from qanuntrace.retrieval import HybridStore, reciprocal_rank_fusion
from qanuntrace.types import LegalRecord, Query


def rec(sid, label=None):
    return LegalRecord.make(sid, 'law', '2026', 'article', sid, 'synthetic',
                            'https://example.org', access_label=label)


def test_fusion_stable_and_deduplicates():
    a, b = rec('a'), rec('b')
    result = reciprocal_rank_fusion((a,b), (b,a))
    assert [x.record.source_id for x in result] == ['a','b']
    assert [x.rank for x in result] == [1,2]


def test_hydrates_from_authority_and_filters_access():
    a, b = rec('a'), rec('b','secret')
    store = HybridStore(MemoryStore((a,b)), lambda q,n: ('b','a'), lambda q,n: ('a','b'), authorized=lambda r: True)
    assert [r.source_id for r in store.search(Query('a'), 2)] == ['a']
    assert {r.source_id for r in store.search(Query('a', access_labels=frozenset({'secret'})), 2)} == {'a','b'}
    with pytest.raises(ValueError):
        reciprocal_rank_fusion((a,), (LegalRecord.make('a','law','other','article','a','different','https://example.org'),))


def test_hybrid_requires_bound_policy():
    with pytest.raises(ValueError):
        HybridStore(MemoryStore(()), lambda q,n: (), lambda q,n: ())
