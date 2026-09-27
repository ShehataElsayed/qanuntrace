from qanuntrace import LegalRecord, Query
from qanuntrace.adapters import MongoStore, QdrantStore


class FakeCursor:
    def __init__(self, rows): self.rows = rows
    def limit(self, n): return self.rows[:n]
class FakeCollection:
    def __init__(self, row): self.row = row
    def find_one(self, query): return self.row if query.get('source_id') == self.row['source_id'] else None
    def find(self, query): return FakeCursor([self.row])

def test_mongo_mapping():
    r = LegalRecord.make('s1', 'i1', 'v1', 'article', '1', 'نص', 'fixture:local')
    store = MongoStore(FakeCollection(r.__dict__), lambda row: LegalRecord(**row))
    assert store.get('s1') == r
    assert list(store.search(Query('نص', instrument_id='i1'), 1)) == [r]

class Point:
    id = 's1'
class Response:
    def __init__(self): self.points = [Point()]
class FakeQdrant:
    def query_points(self, **kwargs): return Response()

def test_qdrant_only_returns_ids():
    from qanuntrace.adapters import MemoryStore
    r = LegalRecord.make('s1', 'i1', 'v1', 'article', '1', 'نص', 'fixture:local')
    store = QdrantStore(FakeQdrant(), 'legal', lambda _: [0.1,0.2], MemoryStore([r]))
    assert list(store.search(Query('نص'), 1)) == [r]
