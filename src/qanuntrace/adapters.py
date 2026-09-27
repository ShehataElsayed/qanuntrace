"""Database adapters. Caller maps rows to LegalRecord and owns access controls.

No adapter creates tables, mutates a database, or downloads legal texts.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from .core import reference_key, search_key
from .types import LegalRecord, Query

Mapper = Callable[[Mapping[str, Any]], LegalRecord]

def _allowed(record: LegalRecord, query: Query) -> bool:
    return ((not query.instrument_id or query.instrument_id == record.instrument_id)
            and (not query.reference or reference_key(query.reference) == reference_key(record.reference))
            and (not query.kind or query.kind == record.kind)
            and (not record.access_label or record.access_label in query.access_labels))

class MemoryStore:
    """Deterministic fixture/small-data adapter; not a substitute for a large search index."""
    def __init__(self, records: Iterable[LegalRecord]):
        items = tuple(records)
        if len({r.source_id for r in items}) != len(items):
            raise ValueError("duplicate source_id")
        self.records = {r.source_id: r for r in items}
    def get(self, source_id: str) -> LegalRecord | None:
        return self.records.get(source_id)
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        terms = search_key(query.text).split()
        ranked = sorted((r for r in self.records.values() if _allowed(r, query)),
                        key=lambda r: sum(search_key(r.exact_text).count(t) for t in terms),
                        reverse=True)
        return ranked[:limit]

class JSONLStore(MemoryStore):
    """Read newline-delimited JSON snapshots from a local file."""
    def __init__(self, path: str | Path, mapper: Mapper | None = None):
        def rows():
            with Path(path).open(encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        row = json.loads(line)
                        yield mapper(row) if mapper else LegalRecord(**row)
        super().__init__(rows())

class SQLAlchemyStore:
    """Read-only SELECT over caller-provided table and validated column mapping.

    Supports SQLAlchemy engines including SQLite and PostgreSQL. Search uses simple
    LIKE for portability; production deployments should supply a full-text backend.
    """
    def __init__(self, engine: Any, table: Any, mapper: Mapper,
                 columns: Mapping[str, str]):
        for key in ("source_id", "instrument_id", "edition_id", "kind", "reference", "exact_text"):
            if key not in columns or columns[key] not in table.c:
                raise ValueError(f"missing mapped column: {key}")
        self.engine, self.table, self.mapper, self.columns = engine, table, mapper, dict(columns)
    def get(self, source_id: str) -> LegalRecord | None:
        from sqlalchemy import select
        stmt = select(self.table).where(self.table.c[self.columns["source_id"]] == source_id).limit(1)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return self.mapper(row) if row else None
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        from sqlalchemy import or_, select
        stmt = select(self.table)
        if query.instrument_id:
            stmt = stmt.where(self.table.c[self.columns["instrument_id"]] == query.instrument_id)
        if query.reference:
            # Caller must map canonical references or handle numeral variants in custom store.
            stmt = stmt.where(self.table.c[self.columns["reference"]] == query.reference)
        if query.kind:
            stmt = stmt.where(self.table.c[self.columns["kind"]] == query.kind)
        terms = query.text.split()[:8]
        if terms:
            col = self.table.c[self.columns["exact_text"]]
            stmt = stmt.where(or_(*(col.ilike("%" + t.replace("%", "\\%")
                                    .replace("_", "\\_") + "%", escape="\\") for t in terms)))
        with self.engine.connect() as conn:
            rows = conn.execute(stmt.limit(limit)).mappings().all()
        return [r for row in rows if _allowed((r := self.mapper(row)), query)]

class SearchStore:
    """Elasticsearch/OpenSearch compatible read-only client; caller owns index and mapper."""
    def __init__(self, client: Any, index: str, mapper: Mapper):
        self.client, self.index, self.mapper = client, index, mapper
    def get(self, source_id: str) -> LegalRecord | None:
        try:
            result = self.client.get(index=self.index, id=source_id)
        except Exception as exc:
            # Never mask transport/auth errors as missing documents.
            if type(exc).__name__ in ("NotFoundError", "NotFoundException"):
                return None
            raise
        return self.mapper(result["_source"])
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        filters = []
        for field, value in (("instrument_id", query.instrument_id), ("kind", query.kind)):
            if value:
                filters.append({"term": {field: value}})
        body = {"query": {"bool": {"must": [{"match": {"exact_text": query.text}}],
                                    "filter": filters}}, "size": limit}
        result = self.client.search(index=self.index, body=body)
        return [r for hit in result["hits"]["hits"]
                if _allowed((r := self.mapper(hit["_source"])), query)]

class VectorStore:
    """Generic vector-client protocol: retrieve IDs only, then hydrate from authoritative store.

    vector_query(query, limit) returns IDs. This avoids treating vector payloads as exact text.
    """
    def __init__(self, vector_query: Callable[[str, int], Iterable[str]], authority: Any):
        self.vector_query, self.authority = vector_query, authority
    def get(self, source_id: str) -> LegalRecord | None:
        return self.authority.get(source_id)
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        ids = list(self.vector_query(query.text, limit))[:limit]
        records = (self.authority.get(source_id) for source_id in ids)
        return [r for r in records if r is not None and _allowed(r, query)]

class MongoStore:
    """PyMongo collection, read-only. Configured field mapper supplies exact records."""
    def __init__(self, collection: Any, mapper: Mapper, source_field: str = "source_id",
                 instrument_field: str = "instrument_id", kind_field: str = "kind"):
        self.collection, self.mapper = collection, mapper
        self.source_field, self.instrument_field, self.kind_field = (
            source_field, instrument_field, kind_field)
    def get(self, source_id: str) -> LegalRecord | None:
        row = self.collection.find_one({self.source_field: source_id})
        return self.mapper(row) if row else None
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]:
        selector: dict[str, Any] = {}
        if query.instrument_id:
            selector[self.instrument_field] = query.instrument_id
        if query.kind:
            selector[self.kind_field] = query.kind
        # No unbounded regex or unknown index assumption. Caller configures Mongo text index.
        if query.text.strip():
            selector["$text"] = {"$search": query.text[:500]}
        return [r for row in self.collection.find(selector).limit(limit)
                if _allowed((r := self.mapper(row)), query)]

class QdrantStore(VectorStore):
    """Qdrant search yields IDs, then source records hydrate from a trusted store."""
    def __init__(self, client: Any, collection: str, embed_query: Callable[[str], list[float]],
                 authority: Any):
        def vector_query(text: str, limit: int) -> Iterable[str]:
            result = client.query_points(collection_name=collection, query=embed_query(text),
                                         limit=limit, with_payload=False)
            return [str(point.id) for point in result.points]
        super().__init__(vector_query, authority)
