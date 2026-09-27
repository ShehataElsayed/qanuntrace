"""Explicit principal-bound guard; database row-level security remains required."""
from __future__ import annotations

from collections.abc import Callable, Iterable

from .core import LegalStore
from .types import LegalRecord, Query


class AuthorizedStore:
    """Deny-by-default wrapper around get and search for an authenticated principal.

    The policy must be backed by server-side ACL/RLS. It must not trust a `Query`'s
    caller-controlled access_labels; downstream indexes must also be tenant-isolated.
    """
    def __init__(self, inner: LegalStore, principal: str,
                 authorize: Callable[[str, LegalRecord], bool]):
        if not principal:
            raise ValueError("authenticated principal required")
        self.inner, self.principal, self.authorize = inner, principal, authorize

    def get(self, source_id: str) -> LegalRecord | None:
        record = self.inner.get(source_id)
        return record if record and self.authorize(self.principal, record) else None

    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        if not 1 <= limit <= 1000:
            raise ValueError("invalid limit")
        # Underlying store is expected to apply its own RLS before reading rows.
        return tuple(record for record in self.inner.search(query, limit)
                     if self.authorize(self.principal, record))[:limit]
