"""Verify signatures made by a trusted upstream signer; do not self-attest origin."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256

from .types import LegalRecord


@dataclass(frozen=True)
class SignedSource:
    source_id: str
    digest: str
    signature: bytes
    key_id: str
    algorithm: str


def canonical_digest(record: LegalRecord) -> str:
    """Bind identity, edition, reference and UTF-8 text with length prefixes."""
    fields = (record.source_id, record.instrument_id, record.edition_id,
              record.kind, record.reference, record.exact_text)
    payload = b"QanunTrace:source:v1\0" + b"".join(
        len(raw).to_bytes(8, "big") + raw for raw in (part.encode("utf-8") for part in fields))
    return sha256(payload).hexdigest()


def verify_signed_source(record: LegalRecord, signed: SignedSource,
                         trusted_verifier: Callable[[str, str, bytes, bytes], bool]) -> bool:
    """Call a deployer-pinned key verifier; a digest alone is not provenance."""
    if (signed.source_id != record.source_id or signed.digest != canonical_digest(record)
        or not signed.key_id or not signed.signature or not signed.algorithm):
        return False
    return trusted_verifier(signed.key_id, signed.algorithm,
                            bytes.fromhex(signed.digest), signed.signature)
