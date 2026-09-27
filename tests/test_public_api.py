import qanuntrace


def test_new_public_entry_points():
    assert qanuntrace.parse_legislative_reference('المادة ٥').article == 5
    assert qanuntrace.version_view((), '2026-09-27').needs_review
    assert qanuntrace.redact('a@example.org').needs_review
