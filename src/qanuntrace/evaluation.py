"""Small gold-set evaluation harness for team-reviewed cases."""
from __future__ import annotations

from dataclasses import dataclass

from .core import Pipeline
from .types import Query


@dataclass(frozen=True)
class EvalCase:
    query: Query
    expected_source_id: str | None
    expected_quote: str | None = None

@dataclass(frozen=True)
class EvalReport:
    total: int
    source_accuracy: float
    exact_quote_accuracy: float
    abstention_accuracy: float
    failures: tuple[int, ...]

def evaluate(pipeline: Pipeline, cases: tuple[EvalCase, ...]) -> EvalReport:
    if not cases:
        raise ValueError("at least one case required")
    source_hits = quote_hits = abstentions = 0
    failures = []
    for i, case in enumerate(cases):
        answer = pipeline.answer(case.query)
        verified = [f for f in answer.findings if f.status == "verified_quote"]
        source_ok = (case.expected_source_id in {f.source_id for f in verified}
                     if case.expected_source_id else answer.status == "abstained")
        quote_ok = (case.expected_quote in {f.quote for f in verified}
                    if case.expected_quote else source_ok)
        source_hits += int(source_ok)
        quote_hits += int(quote_ok)
        abstentions += int(case.expected_source_id is None and answer.status == "abstained")
        if not source_ok or not quote_ok:
            failures.append(i)
    n = len(cases)
    return EvalReport(n, source_hits/n, quote_hits/n, abstentions/n, tuple(failures))
