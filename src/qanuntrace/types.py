"""Data contracts. Exact text is kept separate from retrieval normalization."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

Kind = Literal["article", "judgment", "regulation"]
Relation = Literal["cites", "applies", "distinguishes", "mentions"]
Status = Literal["verified_quote", "needs_review", "rejected", "abstained"]

@dataclass(frozen=True)
class LegalRecord:
    source_id: str
    instrument_id: str
    edition_id: str
    kind: Kind
    reference: str
    exact_text: str
    source_uri: str
    source_hash: str
    effective_from: str | None = None  # ISO yyyy-mm-dd, inclusive
    effective_to: str | None = None    # ISO yyyy-mm-dd, exclusive
    court: str | None = None
    judgment_status: str | None = None
    access_label: str | None = None
    paragraph: str | None = None

    @classmethod
    def make(cls, source_id: str, instrument_id: str, edition_id: str, kind: Kind,
             reference: str, exact_text: str, source_uri: str,
             effective_from: str | None = None, effective_to: str | None = None,
             court: str | None = None, judgment_status: str | None = None,
             access_label: str | None = None, paragraph: str | None = None) -> LegalRecord:
        return cls(source_id, instrument_id, edition_id, kind, reference, exact_text,
                   source_uri, sha256(exact_text.encode("utf-8")).hexdigest(),
                   effective_from, effective_to, court, judgment_status, access_label, paragraph)

@dataclass(frozen=True)
class Query:
    text: str
    instrument_id: str | None = None
    reference: str | None = None
    as_of: str | None = None
    kind: Kind | None = None
    access_labels: frozenset[str] = frozenset()

@dataclass(frozen=True)
class EvidenceProposal:
    source_id: str
    instrument_id: str
    edition_id: str
    reference: str
    start: int
    end: int
    proposed_quote: str
    interpretation: str | None = None
    # Judgment link must be separately reviewed unless sourced by an exact span.
    linked_article_source_id: str | None = None
    relation: Relation | None = None

@dataclass(frozen=True)
class Finding:
    status: Status
    reason: str
    source_id: str | None = None
    quote: str | None = None
    source_uri: str | None = None
    source_hash: str | None = None
    interpretation: str | None = None

@dataclass(frozen=True)
class AuditEvent:
    stage: str
    code: str
    details: dict[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class Answer:
    status: Status
    findings: tuple[Finding, ...]
    text: str
    audit: tuple[AuditEvent, ...]
