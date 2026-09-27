from qanuntrace.cache import CacheKey, VerifiedCache


def test_source_change_invalidates_and_tenants_isolate():
    hashes = {('a','source'): 'h1', ('b','source'): 'h1'}
    cache = VerifiedCache(lambda tenant,source: hashes.get((tenant,source)))
    a = CacheKey.make('a','case-team','source','h1','2020-01-01','2030-01-01','q')
    b = CacheKey.make('b','case-team','source','h1','2020-01-01','2030-01-01','q')
    cache.put(a, 'A'); cache.put(b, 'B')
    hashes['a','source'] = 'h2'
    assert cache.get(a) is None and cache.get(b) == 'B'
    cache.invalidate_source('b','source')
    assert cache.get(b) is None
