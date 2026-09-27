"""Fail-closed legal evidence verification, not a legal opinion engine."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from hashlib import sha256
from typing import Protocol

from .types import Answer, AuditEvent, EvidenceProposal, Finding, LegalRecord, Query, Status


class LegalStore(Protocol):
    def get(self, source_id: str) -> LegalRecord | None: ...
    def search(self, query: Query, limit: int) -> Iterable[LegalRecord]: ...

class Generator(Protocol):
    def propose(self, query: Query, records: tuple[LegalRecord, ...]) -> Iterable[EvidenceProposal]: ...

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def reference_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).translate(_DIGITS).strip()
    return str(int(value)) if re.fullmatch(r"[0-9]+", value) else value

def search_key(value: str) -> str:
    """For ranking only; never use as a legal quotation."""
    value = unicodedata.normalize("NFKC", value).translate(_DIGITS)
    value = "".join(x for x in value if not unicodedata.combining(x))
    return re.sub(r"\s+", " ", value.translate(str.maketrans("إأآٱى", "ااااي"))).strip().lower()

def _finding(status: Status, reason: str, record: LegalRecord | None = None,
             quote: str | None = None, interpretation: str | None = None) -> Finding:
    return Finding(status, reason, record.source_id if record else None, quote,
                   record.source_uri if record else None, record.source_hash if record else None,
                   interpretation)

def verify(store: LegalStore, query: Query, proposed: EvidenceProposal) -> Finding:
    record = store.get(proposed.source_id)
    if record is None:
        return _finding("rejected", "unknown_source_id")
    if sha256(record.exact_text.encode("utf-8")).hexdigest() != record.source_hash:
        return _finding("rejected", "source_hash_mismatch", record)
    if (record.instrument_id != proposed.instrument_id or record.edition_id != proposed.edition_id
        or reference_key(record.reference) != reference_key(proposed.reference)):
        return _finding("rejected", "source_identity_mismatch", record)
    if query.instrument_id and query.instrument_id != record.instrument_id:
        return _finding("rejected", "wrong_instrument", record)
    if query.reference and reference_key(query.reference) != reference_key(record.reference):
        return _finding("rejected", "wrong_article", record)
    if query.kind and query.kind != record.kind:
        return _finding("rejected", "wrong_kind", record)
    if record.access_label and record.access_label not in query.access_labels:
        return _finding("rejected", "access_denied", record)
    if query.as_of:
        if not record.effective_from or not record.effective_to:
            return _finding("needs_review", "unknown_effective_interval", record)
        if not record.effective_from <= query.as_of < record.effective_to:
            return _finding("rejected", "outside_effective_interval", record)
    if (proposed.start < 0 or proposed.end <= proposed.start
        or proposed.end > len(record.exact_text)):
        return _finding("rejected", "invalid_span", record)
    quote = record.exact_text[proposed.start:proposed.end]
    if proposed.proposed_quote != quote:
        return _finding("rejected", "quote_mismatch", record)
    if proposed.linked_article_source_id or proposed.relation:
        if record.kind != "judgment" or not proposed.linked_article_source_id or not proposed.relation:
            return _finding("rejected", "invalid_judgment_link", record)
        article = store.get(proposed.linked_article_source_id)
        if article is None or article.kind not in ("article", "regulation"):
            return _finding("rejected", "missing_linked_article", record)
        if proposed.relation != "mentions" or proposed.interpretation:
            return _finding("needs_review", "judgment_relation_needs_review", record, quote,
                            proposed.interpretation)
        return _finding("needs_review", "mention_not_application", record, quote)
    if proposed.interpretation:
        return _finding("needs_review", "interpretation_not_verified", record, quote,
                        proposed.interpretation)
    return _finding("verified_quote", "verbatim_only", record, quote)

class Pipeline:
    def __init__(self, store: LegalStore, generator: Generator, limit: int = 20) -> None:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        self.store, self.generator, self.limit = store, generator, limit

    def answer(self, query: Query) -> Answer:
        audit: list[AuditEvent] = [AuditEvent("understand", "structured_query",
                          {"has_instrument": str(bool(query.instrument_id)),
                           "has_reference": str(bool(query.reference)),
                           "has_date": str(bool(query.as_of))})]
        records = tuple(self.store.search(query, self.limit))[:self.limit]
        audit.append(AuditEvent("retrieve", "candidates", {"count": str(len(records))}))
        eligible = tuple(r for r in records if
                         (not query.instrument_id or r.instrument_id == query.instrument_id) and
                         (not query.reference or reference_key(r.reference) == reference_key(query.reference)) and
                         (not query.kind or r.kind == query.kind) and
                         (not r.access_label or r.access_label in query.access_labels))
        # Lexical reranking only. No normalized search text is shown as evidence.
        terms = search_key(query.text).split()
        ranked = tuple(sorted(eligible, key=lambda r: sum(search_key(r.exact_text).count(t)
                                                      for t in terms), reverse=True))
        audit.append(AuditEvent("rerank", "eligible", {"count": str(len(ranked))}))
        if not ranked:
            audit.append(AuditEvent("abstain", "no_eligible_records"))
            return Answer("abstained", (), "No verified source was found.", tuple(audit))
        allowed = {r.source_id for r in ranked}
        proposals = tuple(self.generator.propose(query, ranked))
        audit.append(AuditEvent("generate", "proposals", {"count": str(len(proposals))}))
        findings = tuple(verify(self.store, query, p) if p.source_id in allowed
                         else _finding("rejected", "not_in_retrieved_set") for p in proposals)
        audit.extend(AuditEvent("verify", f.reason, {"source_id": f.source_id or ""})
                     for f in findings)
        safe = tuple(f for f in findings if f.status == "verified_quote")
        # Repair is exclusion, never a model rewrite. Review-only text is not published.
        audit.append(AuditEvent("repair", "withheld_unverified",
                                {"count": str(len(findings)-len(safe))}))
        if not safe:
            audit.append(AuditEvent("abstain", "no_verified_quotes"))
            return Answer("abstained", findings, "No verified quotation is available.", tuple(audit))
        text = "\n\n".join(f'[{f.source_id}] "{f.quote}" ({f.source_uri})' for f in safe)
        return Answer("verified_quote", findings, text, tuple(audit))
