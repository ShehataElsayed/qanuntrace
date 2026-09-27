"""Explicit network transfer boundary for remote generator adapters."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .privacy import RedactedText, redact
from .types import LegalRecord, Query


@dataclass(frozen=True)
class TransferDecision:
    allowed: bool
    reason: str
    question: str | None
    records: tuple[tuple[str, str], ...]
    needs_review: bool


def prepare_remote_transfer(query: Query, records: tuple[LegalRecord, ...],
                            *, approved: bool = False,
                            review: Callable[[RedactedText], bool] | None = None
                            ) -> TransferDecision:
    """Never send source text or restore identities here; caller opts in after policy review."""
    if not approved:
        return TransferDecision(False, "transfer_not_approved", None, (), True)
    question = redact(query.text)
    source_texts = tuple(redact(r.exact_text) for r in records)
    if review is None or not all(review(part) for part in (question, *source_texts)):
        return TransferDecision(False, "redaction_review_required", None, (), True)
    return TransferDecision(True, "reviewed_redacted_transfer", question.text,
                            tuple((r.source_id, part.text) for r, part in zip(records, source_texts)),
                            True)
