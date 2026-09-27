import pytest

from qanuntrace.model_bridge import FunctionModel, ProposalBridge
from qanuntrace.types import LegalRecord, Query


def test_local_model_callable_no_unapproved_transfer():
    calls = []
    model = FunctionModel(lambda system, user: calls.append((system,user)) or '[]')
    rec = LegalRecord.make('s','law','v1','article','1','synthetic','https://example.org')
    blocked = ProposalBridge(model, approve_transfer=lambda q,r: False)
    with pytest.raises(PermissionError):
        tuple(blocked.propose(Query('x'), (rec,)))
    assert not calls
    allowed = ProposalBridge(model, approve_transfer=lambda q,r: True)
    assert tuple(allowed.propose(Query('x'), (rec,))) == () and len(calls) == 1
    with pytest.raises(ValueError):
        tuple(ProposalBridge(model, approve_transfer=lambda q,r: True, max_chars=1).propose(Query('x'),(rec,)))
