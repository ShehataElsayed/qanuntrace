from qanuntrace.access import AuthorizedStore
from qanuntrace.adapters import MemoryStore
from qanuntrace.types import LegalRecord, Query


def test_principal_filter_applies_to_get_and_search():
    a = LegalRecord.make('a','law','v1','article','1','synthetic','https://example.org')
    b = LegalRecord.make('b','law','v1','article','2','synthetic','https://example.org')
    store = AuthorizedStore(MemoryStore((a,b)), 'alice', lambda principal, record: record.source_id == 'a')
    assert store.get('a') == a and store.get('b') is None
    assert tuple(store.search(Query('synthetic', access_labels=frozenset({'admin'})), 2)) == (a,)
