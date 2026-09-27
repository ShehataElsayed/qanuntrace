from qanuntrace.gateway import prepare_remote_transfer
from qanuntrace.types import LegalRecord, Query


def test_network_boundary_requires_approval_and_review():
    r = LegalRecord.make('s','law','v1','article','1','اتصل 0501234567','https://example.org')
    q = Query('رقم 0501234567')
    assert not prepare_remote_transfer(q,(r,)).allowed
    assert not prepare_remote_transfer(q,(r,),approved=True).allowed
    accepted = prepare_remote_transfer(q,(r,),approved=True,review=lambda redacted: True)
    assert accepted.allowed and '0501234567' not in repr(accepted)
    assert accepted.records[0][0] == 's'
