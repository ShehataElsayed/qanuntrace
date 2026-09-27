"""Read-only diagnostic report, never a certificate of legal or security fitness."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from time import perf_counter

from .core import LegalStore
from .types import Query


@dataclass(frozen=True)
class HealthReport:
    connected: bool
    sampled: bool
    utf8_valid: bool | None
    hash_valid: bool | None
    latency_ms: float
    warnings: tuple[str, ...]

    def as_json_object(self) -> dict[str, object]:
        return asdict(self)


def health_check(store: LegalStore) -> HealthReport:
    """Sample one source without returning private identifiers or original text."""
    started = perf_counter()
    try:
        records = tuple(store.search(Query(""), 1))[:1]
    except (OSError, RuntimeError, ValueError, TypeError):
        return HealthReport(False, False, None, None,
                            round((perf_counter()-started)*1000, 2), ("connection_or_mapping_failed",))
    elapsed = round((perf_counter()-started)*1000, 2)
    if not records:
        return HealthReport(True, False, None, None, elapsed, ("no_sample_available",))
    record = records[0]
    try:
        raw = record.exact_text.encode("utf-8", "strict")
    except UnicodeError:
        return HealthReport(True, True, False, None, elapsed, ("invalid_utf8",))
    match = sha256(raw).hexdigest() == record.source_hash
    return HealthReport(True, True, True, match, elapsed,
                        () if match else ("hash_mismatch",))
