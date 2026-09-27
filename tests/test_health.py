from qanuntrace.adapters import MemoryStore
from qanuntrace.health import health_check
from qanuntrace.types import LegalRecord


def test_health_report_redacts_sample():
    record = LegalRecord.make('secret-id','law','v1','article','1','PRIVATE BODY','https://example.org')
    report = health_check(MemoryStore((record,)))
    assert report.connected and report.sampled and report.hash_valid
    assert 'PRIVATE BODY' not in repr(report) and 'secret-id' not in repr(report)
    assert report.as_json_object()['connected']
