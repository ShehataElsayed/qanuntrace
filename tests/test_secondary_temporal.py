import pytest

from qanuntrace.secondary import boe_reference
from qanuntrace.temporal import version_view
from qanuntrace.types import LegalRecord


def rec(edition, start, end):
    return LegalRecord.make(edition, 'law', edition, 'article', '5', 'synthetic',
                            'https://example.org/law', start, end)


def test_boe_is_only_secondary_link():
    r = boe_reference('source-5', 'https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/test/1')
    assert r.status == 'unverified_secondary_reference'
    for url in ('http://laws.boe.gov.sa/BoeLaws/x',
                'https://laws.boe.gov.sa.evil.test/BoeLaws/x',
                'https://laws.boe.gov.sa@evil.test/BoeLaws/x'):
        with pytest.raises(ValueError):
            boe_reference('x', url)


def test_temporal_review_and_overlap():
    prior, active = rec('old','2020-01-01','2022-01-01'), rec('new','2022-01-01','2030-01-01')
    view = version_view((prior, active), '2026-09-27')
    assert view.active == (active,) and view.prior == (prior,) and not view.needs_review
    assert version_view((prior,), '2026-09-27').reasons == ('no_active_version',)
    assert 'overlapping_versions' in version_view((prior,rec('overlap','2021-01-01','2030-01-01')), '2021-06-01').reasons
