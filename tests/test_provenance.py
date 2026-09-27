from qanuntrace.provenance import SignedSource, canonical_digest, verify_signed_source
from qanuntrace.types import LegalRecord


def test_signature_requires_pinned_verifier_not_self_hash():
    rec = LegalRecord.make('s','law','2026','article','5','synthetic','https://example.org')
    digest = canonical_digest(rec)
    att = SignedSource('s', digest, b'signed', 'trusted-key', 'test')
    assert verify_signed_source(rec, att, lambda key, algo, message, sig:
                                (key,algo,message,sig) == ('trusted-key','test',bytes.fromhex(digest),b'signed'))
    assert not verify_signed_source(rec, att, lambda *_: False)
    changed = LegalRecord.make('s','law','2027','article','5','synthetic','https://example.org')
    assert not verify_signed_source(changed, att, lambda *_: True)
