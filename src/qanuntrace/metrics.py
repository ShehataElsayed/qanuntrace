"""Deterministic text-level scores; not legal entailment or claim truth."""
from __future__ import annotations

from dataclasses import dataclass

from .types import Answer


@dataclass(frozen=True)
class QuoteMetrics:
    proposals: int
    verified: int
    strict_quote_rate: float | None
    review_only: int


def quote_metrics(answer: Answer) -> QuoteMetrics:
    findings = answer.findings
    verified = sum(f.status == "verified_quote" for f in findings)
    review_only = sum(f.status == "needs_review" for f in findings)
    return QuoteMetrics(len(findings), verified, verified / len(findings) if findings else None,
                        review_only)


@dataclass(frozen=True)
class LabeledAssessment:
    total: int
    faithfulness_agreement: float | None
    relevance_agreement: float | None
    missing_labels: int


def assess_labeled_cases(judged: tuple[tuple[bool | None, bool | None], ...]
                         ) -> LabeledAssessment:
    """Aggregate independent human labels; absent labels cannot be scored."""
    faithful = [f for f, _ in judged if f is not None]
    relevant = [r for _, r in judged if r is not None]
    return LabeledAssessment(len(judged),
                             sum(faithful) / len(faithful) if faithful else None,
                             sum(relevant) / len(relevant) if relevant else None,
                             sum(f is None or r is None for f, r in judged))
