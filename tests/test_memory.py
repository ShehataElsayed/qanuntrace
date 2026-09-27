from qanuntrace.memory import EphemeralCache, ReviewedNote, SQLiteReviewMemory


def test_review_memory_is_tenant_and_hash_scoped(tmp_path):
    db = SQLiteReviewMemory(str(tmp_path/'review.db'))
    note = ReviewedNote('t1','case-1','article-1','hash1','verified link','lawyer','2026-09-27T00:00:00Z')
    db.save(note)
    assert db.get('t1','case-1','hash1') == note
    assert db.get('t2','case-1','hash1') is None
    assert db.get('t1','case-1','hash2') is None
    db.forget('t1','case-1')
    assert db.get('t1','case-1','hash1') is None

def test_cache_bounded_and_source_scoped():
    cache = EphemeralCache(1)
    a = cache.key('tenant','source','h1','query')
    b = cache.key('tenant','source','h2','query')
    cache.put(a,'old')
    cache.put(b,'new')
    assert cache.get(a) is None and cache.get(b) == 'new'
