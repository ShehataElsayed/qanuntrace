"""Source-hash keyed cache; source text and currentness stay in authoritative DB."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class CacheKey:
    tenant: str
    principal_scope: str
    source_id: str
    source_hash: str
    effective_from: str | None
    effective_to: str | None
    query_hash: str

    @classmethod
    def make(cls, tenant: str, principal_scope: str, source_id: str,
             source_hash: str, effective_from: str | None, effective_to: str | None,
             query: str) -> CacheKey:
        if not all((tenant, principal_scope, source_id, source_hash)):
            raise ValueError("tenant, authorization scope and source identity required")
        return cls(tenant, principal_scope, source_id, source_hash, effective_from,
                   effective_to, sha256(query.encode("utf-8")).hexdigest())


class VerifiedCache:
    def __init__(self, current_hash: Callable[[str, str], str | None]):
        self.current_hash = current_hash
        self.items: dict[CacheKey, object] = {}

    def put(self, key: CacheKey, value: object) -> None:
        if self.current_hash(key.tenant, key.source_id) != key.source_hash:
            raise ValueError("stale or unavailable source")
        self.items[key] = value

    def get(self, key: CacheKey) -> object | None:
        if self.current_hash(key.tenant, key.source_id) != key.source_hash:
            self.items.pop(key, None)
            return None
        return self.items.get(key)

    def invalidate_source(self, tenant: str, source_id: str) -> None:
        for key in tuple(self.items):
            if key.tenant == tenant and key.source_id == source_id:
                del self.items[key]
