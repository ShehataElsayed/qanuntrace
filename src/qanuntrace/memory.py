"""Persistent reviewed annotations, not a substitute for legal source evidence."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class ReviewedNote:
    tenant: str
    key: str
    source_id: str
    source_hash: str
    annotation: str
    reviewer: str
    reviewed_at: str

class SQLiteReviewMemory:
    """A local backend for reviewer annotations; deployer owns encryption and tenant ACL.

    Uses a separate DB file and never writes to the authoritative legal corpus.
    Server-side authorization must be enforced by caller before passing a tenant.
    """
    def __init__(self, path: str):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS reviewed_notes (
                tenant TEXT NOT NULL, key TEXT NOT NULL, source_id TEXT NOT NULL,
                source_hash TEXT NOT NULL, annotation TEXT NOT NULL,
                reviewer TEXT NOT NULL, reviewed_at TEXT NOT NULL,
                PRIMARY KEY (tenant, key))''')
    def save(self, note: ReviewedNote) -> None:
        if not all((note.tenant, note.key, note.source_id, note.source_hash,
                    note.reviewer, note.reviewed_at)):
            raise ValueError("review note requires tenant/source/reviewer/time")
        with sqlite3.connect(self.path) as db:
            db.execute('''INSERT INTO reviewed_notes VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant,key) DO UPDATE SET source_id=excluded.source_id,
                source_hash=excluded.source_hash, annotation=excluded.annotation,
                reviewer=excluded.reviewer, reviewed_at=excluded.reviewed_at''',
                (note.tenant, note.key, note.source_id, note.source_hash,
                 note.annotation, note.reviewer, note.reviewed_at))
    def get(self, tenant: str, key: str, current_source_hash: str) -> ReviewedNote | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute('SELECT * FROM reviewed_notes WHERE tenant=? AND key=?',
                             (tenant, key)).fetchone()
        if not row or row[3] != current_source_hash:
            return None
        return ReviewedNote(*row)
    def forget(self, tenant: str, key: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM reviewed_notes WHERE tenant=? AND key=?', (tenant, key))

class EphemeralCache:
    """Small process-local cache with source-hash-based keys, never source authority."""
    def __init__(self, max_items: int = 1000):
        if max_items < 1: raise ValueError("max_items must be positive")
        self.max_items = max_items
        self._items: dict[str, Any] = {}
    @staticmethod
    def key(tenant: str, source_id: str, source_hash: str, query: str) -> str:
        return sha256(json.dumps((tenant,source_id,source_hash,query),
                                 ensure_ascii=False).encode()).hexdigest()
    def put(self, key: str, value: Any) -> None:
        if len(self._items) >= self.max_items and key not in self._items:
            self._items.pop(next(iter(self._items)))
        self._items[key] = value
    def get(self, key: str) -> Any:
        return self._items.get(key)
