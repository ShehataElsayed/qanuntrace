import pytest

from qanuntrace.government import GovernmentAPI, approved_get


def test_api_transport_requires_approved_contract_and_never_guesses_endpoint():
    api = GovernmentAPI('najiz','https://api.example.gov.sa/', 'api.example.gov.sa')
    seen = []
    def fetch(url, headers):
        seen.append((url,headers))
        return b'{"synthetic":true}'
    with pytest.raises(PermissionError):
        approved_get(api, '/approved/path', fetch)
    assert not seen
    result = approved_get(api, '/approved/path', fetch, approved=True)
    assert result.needs_review and result.data == {'synthetic': True}
    assert seen[0][0] == 'https://api.example.gov.sa/approved/path'
    with pytest.raises(ValueError):
        approved_get(api, '//evil.test', fetch, approved=True)
    with pytest.raises(ValueError):
        GovernmentAPI('bad','https://api.example.gov.sa.evil.test','api.example.gov.sa')


def test_host_escape_and_response_limits():
    api = GovernmentAPI('moj','https://api.example.gov.sa/', 'api.example.gov.sa')
    with pytest.raises(ValueError):
        approved_get(api, '/../private', lambda *_: b'{}', approved=True)
    with pytest.raises(ValueError):
        approved_get(api, '/ok', lambda *_: b'X' * 10, approved=True, max_bytes=5)
