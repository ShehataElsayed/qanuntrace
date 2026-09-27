"""Human-review handoff, deliberately not an auto-approval mechanism."""
from __future__ import annotations

from dataclasses import dataclass

from .types import Answer


@dataclass(frozen=True)
class ReviewItem:
    source_id: str | None
    reason: str
    quote: str | None
    source_uri: str | None
    proposed_interpretation: str | None

def review_queue(answer: Answer) -> tuple[ReviewItem, ...]:
    return tuple(ReviewItem(f.source_id, f.reason, f.quote, f.source_uri, f.interpretation)
                 for f in answer.findings if f.status == "needs_review")
