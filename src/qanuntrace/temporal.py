"""Version selection from a caller-curated corpus. Absence does not prove current law."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from .types import LegalRecord


@dataclass(frozen=True)
class VersionView:
    active: tuple[LegalRecord, ...]
    prior: tuple[LegalRecord, ...]
    future: tuple[LegalRecord, ...]
    needs_review: bool
    reasons: tuple[str, ...]


def version_view(records: tuple[LegalRecord, ...], as_of: str) -> VersionView:
    point = date.fromisoformat(as_of)
    if not records:
        return VersionView((), (), (), True, ("no_versions_supplied",))
    key = {(r.instrument_id, r.reference, r.kind) for r in records}
    if len(key) != 1:
        raise ValueError("version view requires one article identity")
    active: list[LegalRecord] = []
    prior: list[LegalRecord] = []
    future: list[LegalRecord] = []
    unknown = False
    intervals: list[tuple[date, date]] = []
    for record in records:
        if not record.effective_from or not record.effective_to:
            unknown = True
            continue
        start, end = date.fromisoformat(record.effective_from), date.fromisoformat(record.effective_to)
        if end <= start:
            raise ValueError("invalid effective interval")
        intervals.append((start, end))
        if start <= point < end:
            active.append(record)
        elif end <= point:
            prior.append(record)
        else:
            future.append(record)
    intervals.sort()
    overlap = any(a[1] > b[0] for a, b in pairwise(intervals))
    reasons = tuple(reason for reason, truth in (("unknown_interval", unknown),
                    ("overlapping_versions", overlap), ("no_active_version", not active)) if truth)
    return VersionView(tuple(active), tuple(prior), tuple(future), bool(reasons), reasons)
