"""Hybrid ranking over already-authorized results; no corpus or remote calls."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .core import LegalStore
from .types import LegalRecord, Query


@dataclass(frozen=True)
class RankedRecord:
    record: LegalRecord
    rank: int
    lexical_rank: int | None
    semantic_rank: int | None


def reciprocal_rank_fusion(lexical: Iterable[LegalRecord], semantic: Iterable[LegalRecord],
                           *, limit: int = 20, k: int = 60,
                           eligible: Callable[[LegalRecord], bool] | None = None
                           ) -> tuple[RankedRecord, ...]:
    """RRF on source IDs; caller must enforce source-level ACL before either retriever runs."""
    if not 1 <= limit <= 1000 or not 1 <= k <= 1000:
        raise ValueError("invalid rank bounds")
    by_id: dict[str, LegalRecord] = {}
    ranks: dict[str, list[int | None]] = {}
    for side, source in enumerate((lexical, semantic)):
        for pos, record in enumerate(source, 1):
            if pos > 1000:
                break
            if eligible and not eligible(record):
                continue
            if record.source_id in ranks and ranks[record.source_id][side] is not None:
                continue
            old = by_id.get(record.source_id)
            if old and (old.source_hash != record.source_hash or old.edition_id != record.edition_id):
                raise ValueError("retrievers disagree on source identity/version")
            by_id[record.source_id] = record
            ranks.setdefault(record.source_id, [None, None])[side] = pos
    ordered = sorted(by_id, key=lambda sid: (-sum(1 / (k+r) for r in ranks[sid] if r is not None), sid))
    return tuple(RankedRecord(by_id[sid], index, ranks[sid][0], ranks[sid][1])
                 for index, sid in enumerate(ordered[:limit], 1))


class HybridStore:
    """Return authorized records from authority; vector and lexical are ID candidates only."""
    def __init__(self, authority: LegalStore,
                 lexical_ids: Callable[[Query, int], Iterable[str]],
                 semantic_ids: Callable[[Query, int], Iterable[str]],
                 authorized: Callable[[LegalRecord], bool] | None = None):
        if authorized is None:
            raise ValueError("an explicit principal-bound authorization policy is required")
        self.authority, self.lexical_ids, self.semantic_ids = authority, lexical_ids, semantic_ids
        self.authorized = authorized

    def get(self, source_id: str) -> LegalRecord | None:
        record = self.authority.get(source_id)
        return record if record and self.authorized(record) else None

    def search(self, query: Query, limit: int) -> tuple[LegalRecord, ...]:
        if not 1 <= limit <= 1000:
            raise ValueError("invalid retrieval limit")
        def hydrate(ids: Iterable[str]) -> tuple[LegalRecord, ...]:
            records: list[LegalRecord] = []
            for source_id in ids:
                if len(records) >= min(1000, limit * 5):
                    break
                record = self.authority.get(source_id)
                if record and self.authorized(record) and (not record.access_label or record.access_label in query.access_labels):
                    records.append(record)
            return tuple(records)
        fused = reciprocal_rank_fusion(hydrate(self.lexical_ids(query, limit * 5)),
                     hydrate(self.semantic_ids(query, limit * 5)), limit=limit)
        return tuple(result.record for result in fused)
